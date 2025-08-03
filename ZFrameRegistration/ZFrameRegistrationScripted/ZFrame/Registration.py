import numpy as np
from scipy.fft import fft2, ifft2

class zf:
    @staticmethod
    def PrintMatrix(matrix):
        print("=============")
        for row in matrix:
            print(", ".join(str(x) for x in row))
        print("=============")
    
    @staticmethod
    def QuaternionToMatrix(q):
        """Convert quaternion to 4x4 matrix.
        
        Args:
            q (list/array): Quaternion [x, y, z, w]
        
        Returns:
            numpy.ndarray: 4x4 transformation matrix
        """
        # Normalize quaternion
        q = np.array(q)
        q = q / np.sqrt(np.sum(q * q))
        x, y, z, w = q

        # Calculate intermediate values
        xx = x * x * 2.0
        xy = x * y * 2.0
        xz = x * z * 2.0
        xw = x * w * 2.0
        yy = y * y * 2.0
        yz = y * z * 2.0
        yw = y * w * 2.0
        zz = z * z * 2.0
        zw = z * w * 2.0

        # Create matrix
        m = np.eye(4)
        m[0, 0] = 1.0 - (yy + zz)
        m[1, 0] = xy + zw
        m[2, 0] = xz - yw
        m[0, 1] = xy - zw
        m[1, 1] = 1.0 - (xx + zz)
        m[2, 1] = yz + xw
        m[0, 2] = xz + yw
        m[1, 2] = yz - xw
        m[2, 2] = 1.0 - (xx + yy)
        
        return m
    
    @staticmethod
    def MatrixToQuaternion(m):
        """Convert 4x4 matrix to quaternion.
        
        Args:
            m (numpy.ndarray): 4x4 transformation matrix
        
        Returns:
            numpy.ndarray: Quaternion [x, y, z, w]
        """
        trace = m[0, 0] + m[1, 1] + m[2, 2]
        q = np.zeros(4)

        if trace > 0:
            s = 0.5 / np.sqrt(trace + 1.0)
            q[3] = 0.25 / s
            q[0] = (m[2, 1] - m[1, 2]) * s
            q[1] = (m[0, 2] - m[2, 0]) * s
            q[2] = (m[1, 0] - m[0, 1]) * s
        else:
            if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
                s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
                q[3] = (m[2, 1] - m[1, 2]) / s
                q[0] = 0.25 * s
                q[1] = (m[0, 1] + m[1, 0]) / s
                q[2] = (m[0, 2] + m[2, 0]) / s
            elif m[1, 1] > m[2, 2]:
                s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
                q[3] = (m[0, 2] - m[2, 0]) / s
                q[0] = (m[0, 1] + m[1, 0]) / s
                q[1] = 0.25 * s
                q[2] = (m[1, 2] + m[2, 1]) / s
            else:
                s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
                q[3] = (m[1, 0] - m[0, 1]) / s
                q[0] = (m[0, 2] + m[2, 0]) / s
                q[1] = (m[1, 2] + m[2, 1]) / s
                q[2] = 0.25 * s
                
        return q
    
    @staticmethod
    def Cross(a, b, c):
        a[0] = b[1]*c[2] - c[1]*b[2]
        a[1] = c[0]*b[2] - b[0]*c[2]
        a[2] = b[0]*c[1] - c[0]*b[1]
        
    @staticmethod
    def IdentityMatrix(matrix):
        matrix[0][0] = 1.0
        matrix[1][0] = 0.0
        matrix[2][0] = 0.0
        matrix[3][0] = 0.0

        matrix[0][1] = 0.0
        matrix[1][1] = 1.0
        matrix[2][1] = 0.0
        matrix[3][1] = 0.0

    @staticmethod
    def QuaternionMultiply(q1, q2):
        """Multiply two quaternions.
        
        Args:
            q1 (numpy.ndarray): First quaternion [x, y, z, w]
            q2 (numpy.ndarray): Second quaternion [x, y, z, w]
            
        Returns:
            numpy.ndarray: Result quaternion [x, y, z, w]
        """
        result = np.zeros(4)
        
        # Extract components for clarity
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        
        # Compute quaternion multiplication
        result[0] = w1*x2 + x1*w2 + y1*z2 - z1*y2  # x
        result[1] = w1*y2 - x1*z2 + y1*w2 + z1*x2  # y
        result[2] = w1*z2 + x1*y2 - y1*x2 + z1*w2  # z
        result[3] = w1*w2 - x1*x2 - y1*y2 - z1*z2  # w
        
        return result

    @staticmethod
    def QuaternionDivide(q1, q2):
        """Divide two quaternions (q1/q2 = q1 * inverse(q2)).
        
        Args:
            q1 (numpy.ndarray): First quaternion [x, y, z, w]
            q2 (numpy.ndarray): Second quaternion [x, y, z, w]
            
        Returns:
            numpy.ndarray: Result quaternion [x, y, z, w]
        """
        # Convert inputs to numpy arrays
        q1 = np.array(q1)
        q2 = np.array(q2)
        
        # Calculate the inverse of q2
        # For unit quaternions, inverse is the conjugate
        q2_norm = np.sum(q2 * q2)
        if q2_norm < 1e-10:  # Avoid division by zero
            return np.array([0.0, 0.0, 0.0, 1.0])
            
        q2_inv = np.array([-q2[0], -q2[1], -q2[2], q2[3]]) / q2_norm
        
        # Multiply q1 by inverse of q2
        result = np.zeros(4)
        result[0] = q1[3]*q2_inv[0] + q1[0]*q2_inv[3] + q1[1]*q2_inv[2] - q1[2]*q2_inv[1]
        result[1] = q1[3]*q2_inv[1] - q1[0]*q2_inv[2] + q1[1]*q2_inv[3] + q1[2]*q2_inv[0]
        result[2] = q1[3]*q2_inv[2] + q1[0]*q2_inv[1] - q1[1]*q2_inv[0] + q1[2]*q2_inv[3]
        result[3] = q1[3]*q2_inv[3] - q1[0]*q2_inv[0] - q1[1]*q2_inv[1] - q1[2]*q2_inv[2]
        
        return result
    
    @staticmethod
    def QuaternionRotateVector(q, v):
        """Rotate a vector by a quaternion rotation.
        
        Args:
            q (numpy.ndarray): Quaternion [x, y, z, w]
            v (numpy.ndarray): Vector to rotate [x, y, z]
            
        Returns:
            numpy.ndarray: Rotated vector [x, y, z]
        """
        # Extract quaternion components
        qx, qy, qz, qw = q
        
        # Compute quaternion multiplication: q * [v,0] * q^(-1)
        t = 2.0 * np.cross([qx, qy, qz], v)
        return v + qw * t + np.cross([qx, qy, qz], t)    
        
class ZFrameRegistration:
    def __init__(self, numFiducials=7):
        self.numFiducials = numFiducials
        self.InputImage = None
        self.InputImageDim = [0, 0, 0]
        self.InputImageTrans = None
        self.frameTopology = None
        self.manualRegistration = False
        self.zFrameFids = None
        self.ZOrientationBase = [0, 0, 0, 1]  # Default quaternion
        
        # Constants
        self.MEPSILON = 1e-10
    
    def SetFrameTopology(self, frameTopology):
        self.frameTopology = frameTopology
    
    def SetInputImage(self, inputImage, transform):
        self.InputImage = inputImage.astype(int)
        self.InputImageDim = list(inputImage.shape)
        self.InputImageTrans = transform
        
    def SetOrientationBase(self, orientation):
        self.ZOrientationBase = orientation

    def Register(self, sliceRange):
        """Register Z-frame fiducials across multiple slices and compute average transformation.
        
        Args:
            range (list): [start_slice, end_slice] range of slices to process
            
        Returns:
            tuple: (success, Zposition, Zorientation) where:
                - success is a boolean indicating if registration was successful
                - Zposition is a numpy array [x,y,z] of the estimated position
                - Zorientation is a numpy array [x,y,z,w] quaternion of the estimated orientation
        """
        xsize, ysize, zsize = self.InputImageDim
        
        # Get image transformation matrix components
        tx = self.InputImageTrans[0][0]
        ty = self.InputImageTrans[1][0]
        tz = self.InputImageTrans[2][0]
        sx = self.InputImageTrans[0][1]
        sy = self.InputImageTrans[1][1]
        sz = self.InputImageTrans[2][1]
        nx = self.InputImageTrans[0][2]
        ny = self.InputImageTrans[1][2]
        nz = self.InputImageTrans[2][2]
        px = self.InputImageTrans[0][3]
        py = self.InputImageTrans[1][3]
        pz = self.InputImageTrans[2][3]
        
        # Normalize vectors
        psi = np.sqrt(tx*tx + ty*ty + tz*tz)
        psj = np.sqrt(sx*sx + sy*sy + sz*sz)
        psk = np.sqrt(nx*nx + ny*ny + nz*nz)
        ntx, nty, ntz = tx/psi, ty/psi, tz/psi
        nsx, nsy, nsz = sx/psj, sy/psj, sz/psj
        nnx, nny, nnz = nx/psk, ny/psk, nz/psk

        # Initialize matrices for averaging quaternions
        n = 0
        T = np.zeros((4, 4))  # Symmetric matrix for quaternion averaging
        P = np.zeros(3)  # Position accumulator
        
        # Create transformation matrix
        matrix = np.eye(4)
        matrix[0:3, 0] = [ntx, nty, ntz]
        matrix[0:3, 1] = [nsx, nsy, nsz]
        matrix[0:3, 2] = [nnx, nny, nnz]
        
        # Process each slice in range
        print(f"Processing slices from {sliceRange[0]} to {sliceRange[1]}")
        for slindex in range(sliceRange[0], sliceRange[1]):
            print(f"=== Current Slice Index: {slindex} ===")
            # Calculate image center offset
            hfovi = psi * (self.InputImageDim[0]-1) / 2.0
            hfovj = psj * (self.InputImageDim[1]-1) / 2.0
            offsetk = psk * slindex
            
            # Calculate center coordinates
            cx = ntx * hfovi + nsx * hfovj + nnx * offsetk
            cy = nty * hfovi + nsy * hfovj + nny * offsetk
            cz = ntz * hfovi + nsz * hfovj + nnz * offsetk
            
            # Initialize position and quaternion for this slice
            quaternion = zf.MatrixToQuaternion(matrix)
            position = [px + cx, py + cy, pz + cz]
            
            # Get current slice data
            if 0 <= slindex < zsize:
                current_slice = self.InputImage[:, :, slindex]
            else:
                return False
            
            # Initialize for this slice
            self.Init(xsize, ysize)
            
            # Register this slice
            spacing = [psi, psj, psk]
            if self.RegisterQuaternion(position, quaternion, self.ZOrientationBase,
                                    current_slice, self.InputImageDim, spacing):
                # Accumulate position
                P += np.array(position)
                
                # Update moment of inertia matrix T
                q = np.array(quaternion)
                T += np.outer(q, q)
                n += 1
            print(f"=== End Slice Index: {slindex} ===\n")
                
        if n <= 0:
            return False, None, None
            
        # Average position and normalize T matrix
        P /= float(n)
        T /= float(n)

        # Calculate eigenvalues and eigenvectors of T matrix
        eigenvals, eigenvecs = np.linalg.eigh(T)
        
        # Find maximum eigenvalue index
        max_idx = np.argmax(eigenvals)

        # Create output arrays
        Zposition = P
        Zorientation = eigenvecs[:, max_idx]
        
        # Force alignment with Superior direction (0,0,1)
        # TODO: This is to ensure orientation is correct. There should be some kind of parameter for this.
        # Convert quaternion to rotation matrix to check orientation
        transform_matrix = np.eye(4)
        transform_matrix[:3, :3] = zf.QuaternionToMatrix(Zorientation)[:3, :3]
        
        # Get the Z direction (third column of rotation matrix)
        z_direction = transform_matrix[:3, 2]
        
        # If Z direction is pointing opposite to superior direction (0,0,1)
        if np.dot(z_direction, np.array([0, 0, 1])) < 0:
            print("ZFrameRegistration - Correcting orientation to point superior")
            rot_matrix = np.array([
                [-1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ])
            # Apply the rotation
            new_transform = np.dot(transform_matrix, rot_matrix)
            # Convert back to quaternion
            Zorientation = zf.MatrixToQuaternion(new_transform)
        
        return True, Zposition, Zorientation

    def Init(self, xsize, ysize):
        """Initialize correlation kernel and perform FFT operations for fiducial detection.
        
        Args:
            xsize (int): Width of the image
            ysize (int): Height of the image
        """
        # Define 11x11 correlation kernel for fiducial detection
        kernel = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0],
            [0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0],
            [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
            [0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
            [0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
            [0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
            [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
            [0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0],
            [0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0]
        ])

        # Create mask image and initialize to zero
        self.MaskImage = np.zeros((xsize, ysize))
        
        # Copy correlation kernel to center of mask image
        x_start = (xsize // 2) - 5
        y_start = (ysize // 2) - 5
        self.MaskImage[x_start:x_start+11, y_start:y_start+11] = kernel

        # Transform mask to frequency domain using FFT
        # Note: numpy's fft2 automatically handles the complex components
        mask_fft = fft2(self.MaskImage)
        
        # Get real and imaginary components
        self.MFreal = np.real(mask_fft)
        self.MFimag = np.imag(mask_fft)
        
        # Conjugate and normalize the mask
        self.MFimag *= -1
        max_absolute = np.max(np.abs(mask_fft))
        self.MFreal /= max_absolute
        self.MFimag /= max_absolute

    def RegisterQuaternion(self, position, quaternion, ZquaternionBase, SourceImage, dimension, spacing):
        """Register the Z-frame using quaternion representation.
        
        Args:
            position (list): [x, y, z] position vector
            quaternion (list): [x, y, z, w] current orientation quaternion
            ZquaternionBase (list): [x, y, z, w] base orientation quaternion
            SourceImage (numpy.ndarray): Input image data
            dimension (list): [x, y, z] image dimensions
            spacing (list): [x, y, z] pixel spacing
            
        Returns:
            bool: True if registration successful, False if failed
        """
        # Convert input position and orientations to numpy arrays
        Iposition = np.array(position)
        Iorientation = np.array(quaternion)
        ZorientationBase = np.array(ZquaternionBase)
        
        # Find the self.numFiducials Z-frame fiducial intercept artifacts in the image
        print("ZTrackerTransform - Searching fiducials...")
        Zcoordinates, tZcoordinates = self.LocateFiducials(SourceImage, dimension[0], dimension[1])
        if Zcoordinates is None:
            print("ZTrackerTransform::onEventGenerated - Fiducials not detected. No frame lock on this image.")
            return False
        
        # Check that the fiducial geometry makes sense
        print("ZTrackerTransform - Checking the fiducial geometries...")
        print(f"Zcoordinates: {Zcoordinates}")
        if not self.CheckFiducialGeometry(Zcoordinates, dimension[0], dimension[1]):
            print("ZTrackerTransform::onEventGenerated - Bad fiducial geometry. No frame lock on this image.")
            return False
        
        # Transform pixel coordinates into spatial coordinates
        for i in range(self.numFiducials):
            # Put the image origin at the center
            tZcoordinates[i][0] = float(tZcoordinates[i][0]) - float(dimension[0]/2)
            tZcoordinates[i][1] = float(tZcoordinates[i][1]) - float(dimension[1]/2)
            
            # Scale coordinates by pixel size
            tZcoordinates[i][0] *= spacing[0]
            tZcoordinates[i][1] *= spacing[1]
        
        # Compute relative pose between the Z-frame and the current image
        Zposition, Zorientation = self.LocalizeFrame(tZcoordinates)
        if Zposition is None or Zorientation is None:
            print("ZTrackerTransform::onEventGenerated - Could not localize the frame. Skipping this one.")
            return False
        
        # Compute the Z-frame position in the image (RAS) coordinate system
        # Rotate vector using quaternion rotation
        rotated_position = zf.QuaternionRotateVector(Iorientation, Zposition)
        Zposition = Iposition + rotated_position
        
        # Combine orientations
        Zorientation = zf.QuaternionMultiply(Iorientation, Zorientation)
        
        # Calculate rotation from the base orientation
        Zorientation = zf.QuaternionDivide(Zorientation, ZorientationBase)
        
        # Update the output parameters
        position[0] = Zposition[0]
        position[1] = Zposition[1]
        position[2] = Zposition[2]
        quaternion[0] = Zorientation[0]
        quaternion[1] = Zorientation[1]
        quaternion[2] = Zorientation[2]
        quaternion[3] = Zorientation[3]
        
        return True

    def LocateFiducials(self, SourceImage, xsize, ysize):
        """Locate the seven line fiducial intercepts in the Z-frame.
        
        Args:
            SourceImage (numpy.ndarray): Input image matrix
            xsize (int): Width of the image in pixels
            ysize (int): Height of the image in pixels
            
        Returns:
            tuple: (Zcoordinates, tZcoordinates) where each is a list of 7 [x,y] coordinates,
                or (None, None) if detection fails
        """
        # Initialize coordinate arrays
        Zcoordinates = [[0, 0] for _ in range(self.numFiducials)]
        tZcoordinates = [[0.0, 0.0] for _ in range(self.numFiducials)]
        
        # Transform the MR image to frequency domain (k-space)
        image_fft = fft2(SourceImage)
        IFreal = np.real(image_fft)
        IFimag = np.imag(image_fft)
        
        # Normalize the image
        max_absolute = np.max(np.abs(image_fft))
        if max_absolute < self.MEPSILON:
            print("ZTrackerTransform::LocateFiducials - divide by zero.")
            return None, None
            
        IFreal /= max_absolute
        IFimag /= max_absolute
        
        # Pointwise multiply Image and Mask in k-space
        PFreal = IFreal * self.MFreal - IFimag * self.MFimag
        PFimag = IFreal * self.MFimag + IFimag * self.MFreal
        
        # Invert product back to spatial domain
        product_ifft = ifft2(PFreal + 1j * PFimag)
        PIreal = np.real(product_ifft)
        
        # FFTSHIFT: exchange diagonally-opposite image quadrants
        PIreal = np.fft.fftshift(PIreal)
        
        # Normalize result
        max_absolute = np.max(np.abs(PIreal))
        if max_absolute < self.MEPSILON:
            print("ZTrackerTransform::LocateFiducials - divide by zero.")
            return None, None
            
        PIreal /= max_absolute
        
        # Find the top self.numFiducials peak image values
        peak_count = 0
        for i in range(self.numFiducials):
            # Find next peak value and its coordinates
            peak_val, peak_coords = self.FindMax(PIreal)
            Zcoordinates[i] = list(peak_coords)
            
            # Define block neighborhood around peak
            rstart = max(0, peak_coords[0] - 10)
            rstop = min(xsize - 1, peak_coords[0] + 10)
            cstart = max(0, peak_coords[1] - 10)
            cstop = min(ysize - 1, peak_coords[1] + 10)
            
            # Check if this is a local maximum
            if peak_val < self.MEPSILON:
                print("Registration::OrderFidPoints - peak value is zero.")
                return None, None
                
            # Check peak prominence
            offpeak1 = (peak_val - PIreal[rstart, cstart]) / peak_val
            offpeak2 = (peak_val - PIreal[rstart, cstop]) / peak_val
            offpeak3 = (peak_val - PIreal[rstop, cstart]) / peak_val
            offpeak4 = (peak_val - PIreal[rstop, cstop]) / peak_val
            
            if offpeak1 < 0.3 or offpeak2 < 0.3 or offpeak3 < 0.3 or offpeak4 < 0.3:
                i -= 1  # Try again for this index
                print("Registration::LocateFiducials - Bad Peak.")
                peak_count += 1
                if peak_count > 10:
                    return None, None
                continue
                
            # Find subpixel coordinates of the peak
            tZcoordinates[i] = self.FindSubPixelPeak(
                peak_coords,
                peak_val,
                PIreal[peak_coords[0]-1, peak_coords[1]],
                PIreal[peak_coords[0]+1, peak_coords[1]],
                PIreal[peak_coords[0], peak_coords[1]-1],
                PIreal[peak_coords[0], peak_coords[1]+1]
            )
            
            # Zero out this peak region
            PIreal[rstart:rstop+1, cstart:cstop+1] = 0.0
        
        # Find center of the pattern
        center = self.FindFidCentre(tZcoordinates)
        
        # Find corner points and order all points
        self.FindFidCorners(tZcoordinates, center)
        self.OrderFidPoints(tZcoordinates, center[0], center[1])
        
        # Update integer coordinates
        for i in range(self.numFiducials):
            Zcoordinates[i] = [int(tZcoordinates[i][0]), int(tZcoordinates[i][1])]
        
        return Zcoordinates, tZcoordinates

    def FindSubPixelPeak(self, peak_coords, Y0, Yx1, Yx2, Yy1, Yy2):
        """Find the subpixel coordinates of the peak using parabolic fitting.
        
        Args:
            peak_coords (list): [x, y] integer coordinates of the peak
            Y0 (float): Peak value
            Yx1 (float): Value at x+1
            Yx2 (float): Value at x-1
            Yy1 (float): Value at y+1
            Yy2 (float): Value at y-1
        
        Returns:
            list: [x, y] coordinates with subpixel accuracy
        """
        # Calculate subpixel shifts using parabolic fitting
        Xshift = (0.5 * (Yx1 - Yx2)) / (Yx1 + Yx2 - 2.0 * Y0)
        Yshift = (0.5 * (Yy1 - Yy2)) / (Yy1 + Yy2 - 2.0 * Y0)
        
        # Check if shifts are within valid range
        if abs(Xshift) > 1.0 or abs(Yshift) > 1.0:
            print("Registration::FindSubPixelPeak - subpixel peak out of range.")
            return [float(peak_coords[0]), float(peak_coords[1])]
        
        # Return coordinates with subpixel accuracy
        return [float(peak_coords[0]) + Xshift, float(peak_coords[1]) + Yshift]

    def CheckFiducialGeometry(self, Zcoordinates, xsize, ysize):
        """Check the geometry of the fiducial pattern to be sure that it is valid.
        
        Args:
            Zcoordinates (list): List of seven [x,y] fiducial coordinates
            xsize (int): Width of the image in pixels
            ysize (int): Height of the image in pixels
            
        Returns:
            bool: True if the point geometry is valid, False otherwise
        """
        # First check that the coordinates are in range
        for coord in Zcoordinates:
            if (coord[0] < 0 or coord[0] >= ysize or 
                coord[1] < 0 or coord[1] >= xsize):
                print("Registration::CheckFiducialGeometry - fiducial coordinates out of range.")
                return False

        # Helper function to create normalized vector between two points
        def get_normalized_vector(p1, p2):
            vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            norm = np.linalg.norm(vector)
            return vector / norm if norm != self.MEPSILON else vector

        if self.numFiducials == 7:
            # Get corner points
            P1 = np.array(Zcoordinates[0])
            P3 = np.array(Zcoordinates[2])
            P5 = np.array(Zcoordinates[4])
            P7 = np.array(Zcoordinates[6])

            # Calculate normalized direction vectors
            D71 = get_normalized_vector(P1, P7)
            D53 = get_normalized_vector(P3, P5)
            D13 = get_normalized_vector(P3, P1)
            D75 = get_normalized_vector(P5, P7)

            # Check that opposite edges are within 10 degrees of parallel
            # using dot product (cos of angle between vectors)
            dotp = np.dot(D71, D53)
            dotp = abs(dotp)
            if dotp < np.cos(5.0 * np.pi / 180.0):
                return False

            dotp = np.dot(D13, D75)
            dotp = abs(dotp)
            if dotp < np.cos(5.0 * np.pi / 180.0):
                return False
        elif self.numFiducials == 9:
            # TODO: Implement 9-fiducial geometry check
            print("Registration::CheckFiducialGeometry - Skipping 9-fiducial geometry check.")
            return True
        else:
            return False

        return True

    def FindFidCentre(self, points):
        """Find the centre of the fiducial pattern.
        
        A cross-sectional image will intercept each of the Z-frame's seven line fiducials.
        Once these seven intercepts are detected, this method computes the centre of the
        region bounded by these points.
        
        Args:
            points (list): List of seven [x,y] fiducial coordinates
            
        Returns:
            list: [x, y] coordinates of the center point
        """
        # Initialize min/max values with the first point
        minrow = maxrow = points[0][0]
        mincol = maxcol = points[0][1]
        
        # Find the bounding rectangle
        for point in points:
            # Find minimum and maximum row coordinates
            minrow = min(minrow, point[0])
            maxrow = max(maxrow, point[0])
            
            # Find minimum and maximum column coordinates
            mincol = min(mincol, point[1])
            maxcol = max(maxcol, point[1])
        
        # Return center of bounding rectangle
        rmid = (minrow + maxrow)/2.0
        cmid = (mincol + maxcol)/2.0
        return rmid, cmid

    def FindFidCorners(self, points, pmid):
        """Identify the four corner fiducials based on Z-frame geometry.
        
        Args:
            points (list): List of seven [x,y] fiducial coordinates
            pmid (tuple): (x,y) coordinates of the center point
        """
        # Compute distances between each fiducial and the midpoint
        distances = [self.CoordDistance(point, pmid) for point in points]
        
        # Sort points by distance from center (descending order)
        # Use bubble sort to match original implementation
        swapped = True
        while swapped:
            swapped = False
            for i in range(6):  # len(points)-1
                if distances[i] < distances[i+1]:
                    # Swap distances
                    distances[i], distances[i+1] = distances[i+1], distances[i]
                    # Swap corresponding coordinates
                    points[i], points[i+1] = points[i+1], points[i]
                    swapped = True
        
        # Choose the order of the corners based on their separation distance
        # First find the closest point to first corner in the list
        pdist1 = self.CoordDistance(points[0], points[1])
        pdist2 = self.CoordDistance(points[0], points[2])
        
        # Swap points[1] and points[2] if needed
        if pdist1 > pdist2:
            points[1], points[2] = points[2], points[1]
        
        # Find closest point (of third or fourth) to second corner in list
        pdist1 = self.CoordDistance(points[1], points[2])
        pdist2 = self.CoordDistance(points[1], points[3])
        
        # Swap points[2] and points[3] if needed
        if pdist1 > pdist2:
            points[2], points[3] = points[3], points[2]

    def CoordDistance(self, p1, p2):
        """Calculate Euclidean distance between two points.
        
        Args:
            p1 (list/array): First point coordinates [x, y]
            p2 (list/array): Second point coordinates [x, y]
            
        Returns:
            float: Euclidean distance between the points
        """
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return np.sqrt(dx*dx + dy*dy)

    def OrderFidPoints(self, points, rmid, cmid):
        """Put the fiducial coordinate point list in sequential order by matching the
        three remaining points to their neighboring ordered corner points.
        
        Args:
            points (list): List of seven [x,y] fiducial coordinates
            rmid (float): The center of the fiducial pattern in the row coordinate
            cmid (float): The center of the fiducial pattern in the column coordinate
        """
        if self.numFiducials == 7:
            # Initialize prototype index lists
            pall = [0, -1, 1, -1, 2, -1, 3, -1, 0]  # prototype index list for all points
            pother = [4, 5, 6]  # indices of points other than corners
                
            # Find fiducial points that fit between the corners
            for i in range(0, 7, 2):
                for j in range(3):
                    if pother[j] == -1:
                        # This point has already been placed
                        continue
                        
                    cdist = self.CoordDistance(points[pall[i]], points[pall[i+2]])
                    pdist1 = self.CoordDistance(points[pall[i]], points[pother[j]])
                    pdist2 = self.CoordDistance(points[pall[i+2]], points[pother[j]])
                    
                    # Check for divide by zero
                    if cdist < self.MEPSILON:
                        print("Registration::OrderFidPoints - divide by zero.")
                        continue
                        
                    if ((pdist1 + pdist2) / cdist) < 1.05:
                        pall[i+1] = pother[j]
                        pother[j] = -1
                        break
            
            # Find the -1 that marks the two corner points without an intermediate fiducial
            for i in range(1, 9):
                if pall[i] == -1:
                    break
            
            # Determine direction to order points (clockwise in image)
            d1x = points[pall[0]][0] - rmid
            d1y = points[pall[0]][1] - cmid
            d2x = points[pall[2]][0] - rmid
            d2y = points[pall[2]][1] - cmid
            nvecz = (d1x * d2y - d2x * d1y)
            
            # Set direction based on z-coordinate
            direction = -1 if nvecz < 0 else 1
            
            # Create new ordered point list
            pall2 = []
            curr_i = i
            for _ in range(7):
                curr_i += direction
                if curr_i == -1:
                    curr_i = 7
                if curr_i == 9:
                    curr_i = 1
                pall2.append(pall[curr_i])
            
            # Create temporary points array and copy ordered points
            points_temp = [[points[idx][0], points[idx][1]] for idx in pall2]
            
            # Update original points array with ordered points
            for i in range(7):
                points[i][0] = points_temp[i][0]
                points[i][1] = points_temp[i][1]
        elif self.numFiducials == 9:
            # Initialize arrays for sorting
            sorter_array = [9, 1, 4, 6, 0, 0, 0, 0, 0]  # Initial indices for corner points
            sorted_points = [True, True, True, True, False, False, False, False, False]
            
            # Find the 5 remaining non-corner fiducial points (Fid 2, 3, 5, 7, 8)
            
            # First, find point closest to points[1] (either Fid #1 or Fid #9)
            shortest_dist = 10000
            closest_index = 0
            
            for i in range(4, 9):
                coord_dist = self.CoordDistance(points[1], points[i])
                if coord_dist < shortest_dist:
                    shortest_dist = coord_dist
                    closest_index = i
            
            sorter_array[closest_index] = 2  # Label index in sorter array
            sorted_points[closest_index] = True
            
            # Find second closest point to points[1] (either Fid #2 or Fid #8)
            shortest_dist = 10000
            for i in range(4, 9):
                if not sorted_points[i]:
                    coord_dist = self.CoordDistance(points[1], points[i])
                    if coord_dist < shortest_dist:
                        shortest_dist = coord_dist
                        closest_index = i
            
            sorter_array[closest_index] = 3
            sorted_points[closest_index] = True
            
            # Find point closest to points[2] (center of top row - Fid #5)
            shortest_dist = 10000
            for i in range(4, 9):
                if not sorted_points[i]:
                    coord_dist = self.CoordDistance(points[2], points[i])
                    if coord_dist < shortest_dist:
                        shortest_dist = coord_dist
                        closest_index = i
            
            sorter_array[closest_index] = 5
            sorted_points[closest_index] = True
            
            # Find point closest to points[0] (Fid #8 if points[0] is Fid #9; Fid #2 otherwise)
            shortest_dist = 10000
            for i in range(4, 9):
                if not sorted_points[i]:
                    coord_dist = self.CoordDistance(points[0], points[i])
                    if coord_dist < shortest_dist:
                        shortest_dist = coord_dist
                        closest_index = i
            
            sorter_array[closest_index] = 8
            sorted_points[closest_index] = True
            
            # Last unsorted point is Fid #7 or Fid #3
            for i in range(4, 9):
                if not sorted_points[i]:
                    sorter_array[i] = 7
                    sorted_points[i] = True
            
            # Sort points based on sorter_array
            # Create list of (index, point) pairs
            pairs = [(sorter_array[i], [points[i][0], points[i][1]]) 
                    for i in range(9)]
            
            # Sort pairs based on index
            pairs.sort(key=lambda x: x[0])
            
            # Update points with sorted coordinates
            for i in range(9):
                points[i][0] = pairs[i][1][0]
                points[i][1] = pairs[i][1][1]
            
            # Order points so first fiducial is at bottom left corner
            if points[0][0] > points[8][0]:
                # Reverse array if x-coordinate of first point is greater than last
                points.reverse()
            
            # Debug output
            print("points[]:")
            for i in range(9):
                print(f"sorted points[{points[i][0]}][{points[i][1]}]")

    def LocalizeFrame(self, Zcoordinates):
        """Compute the pose of the fiducial frame relative to the image plane.
        
        Uses an adaptation of an algorithm presented by Susil et al.:
        "A Single image Registration Method for CT-Guided Interventions", MICCAI 1999.
        
        Args:
            Zcoordinates (list): List of seven [x,y] fiducial coordinates
            
        Returns:
            tuple: (Zposition, Zorientation) where:
                - Zposition is a numpy array [x,y,z] of the estimated position
                - Zorientation is a numpy array [x,y,z,w] quaternion of the estimated orientation
                Returns (None, None) if computation fails
        """
        # Initialize vectors for computations
        def make_vector(x, y, z=0.0):
            return np.array([x, y, z])
        
        # 7 fiducial version
        if self.numFiducials == 7:
            # --- Compute diagonal points in the z-frame coordinates ---
            # SIDE 1
            # Map the three points for this z-fiducial
            Pz1 = make_vector(Zcoordinates[0][0], Zcoordinates[0][1])
            Pz2 = make_vector(Zcoordinates[1][0], Zcoordinates[1][1])
            Pz3 = make_vector(Zcoordinates[2][0], Zcoordinates[2][1])
            
            # Origin and direction vector of diagonal fiducial
            Oz = make_vector(*self.frameTopology[0])
            Vz = make_vector(*self.frameTopology[3])
            
            # Solve for the diagonal intercept in Z-frame coordinates
            # Assume distance between parallel fiducials is self.frameTopology[0][1]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[0][1]*2)
            P2f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P2f is None:
                return None, None
                
            # BASE
            Pz1 = make_vector(Zcoordinates[2][0], Zcoordinates[2][1])
            Pz2 = make_vector(Zcoordinates[3][0], Zcoordinates[3][1])
            Pz3 = make_vector(Zcoordinates[4][0], Zcoordinates[4][1])
            
            Oz = make_vector(*self.frameTopology[1])
            Vz = make_vector(*self.frameTopology[4])
            
            # Assume distance between parallel fiducials is self.frameTopology[1][0]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[1][0]*2)
            P4f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P4f is None:
                return None, None
                
            # SIDE 2
            Pz1 = make_vector(Zcoordinates[4][0], Zcoordinates[4][1])
            Pz2 = make_vector(Zcoordinates[5][0], Zcoordinates[5][1])
            Pz3 = make_vector(Zcoordinates[6][0], Zcoordinates[6][1])
            
            Oz = make_vector(*self.frameTopology[2])
            Vz = make_vector(*self.frameTopology[5])
            
            # Assume distance between parallel fiducials is self.frameTopology[2][1]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[2][1]*2)
            P6f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P6f is None:
                return None, None
            
            # --- Compute Transformation Between Image and Frame ---
            # Compute z-frame cross section coordinate frame
            Vx = P2f - P6f
            Vy = P4f - P6f

            # Normalize Vx first
            Vx = Vx / np.linalg.norm(Vx)

            # Compute Vz using normalized Vx
            Vz = np.cross(Vx, Vy)
            Vz = Vz / np.linalg.norm(Vz)

            # Recompute Vy to ensure perfect orthogonality
            Vy = np.cross(Vz, Vx)
            # Vy is automatically normalized since it's cross product of two unit vectors
            
            # Create rotation matrix and convert to quaternion
            rotation_matrix = np.column_stack((Vx, Vy, Vz))
            transform_matrix = np.eye(4)  # Initialize 4x4 matrix
            transform_matrix[:3, :3] = rotation_matrix
            Qft = zf.MatrixToQuaternion(transform_matrix) 
            
            # Compute image cross-section coordinate frame
            Pz1 = make_vector(Zcoordinates[1][0], Zcoordinates[1][1])
            Pz2 = make_vector(Zcoordinates[3][0], Zcoordinates[3][1])
            Pz3 = make_vector(Zcoordinates[5][0], Zcoordinates[5][1])
            
            Vx = Pz1 - Pz3
            Vy = Pz2 - Pz3
            Vz = np.cross(Vx, Vy)
            Vy = np.cross(Vz, Vx)

            Vx_norm = np.linalg.norm(Vx)
            Vy_norm = np.linalg.norm(Vy)
            Vz_norm = np.linalg.norm(Vz)

            if Vx_norm < self.MEPSILON or Vy_norm < self.MEPSILON or Vz_norm < self.MEPSILON:
                print("Registration::LocalizeFrame - Vx, Vy, or Vz is too small, something is wrong.")
                return None, None

            # Normalize vectors
            Vx = Vx / Vx_norm
            Vy = Vy / Vy_norm
            Vz = Vz / Vz_norm
            
            # Create rotation matrix and convert to quaternion
            rotation_matrix = np.column_stack((Vx, Vy, Vz))
            transform_matrix = np.eye(4)
            transform_matrix[:3, :3] = rotation_matrix
            Qit = zf.MatrixToQuaternion(transform_matrix)
            
            # Compute rotation between frame and image
            Zorientation = zf.QuaternionDivide(Qit, Qft)
            
            # Check rotation angle
            angle = 2 * np.arccos(Zorientation[3])  # w component
            if abs(angle) > 15.0:
                print("Registration::LocalizeFrame - Rotation angle too large, something is wrong.")
                return None, None
            
            # Compute axis of rotation
            if angle == 0.0:
                axis = np.array([1.0, 0.0, 0.0])
            else:
                denom = np.sqrt(1 - Zorientation[3] * Zorientation[3])
                if abs(denom) < self.MEPSILON:
                    print("Registration::LocalizeFrame - Division by zero in axis calculation.")
                    return None, None
                axis = Zorientation[:3] / denom
                axis = axis / np.linalg.norm(axis)
            
            print(f"Rotation Angle [degrees]: {angle * 180.0 / np.pi}")
            print(f"Rotation Axis: [{axis[0]}, {axis[1]}, {axis[2]}]")
            
            # Compute translational component
            # Centroid of triangle in frame coordinates
            Cf = (P2f + P4f + P6f) / 3.0
            
            # Centroid of frame triangle in image coordinates
            Cfi = zf.QuaternionRotateVector(Zorientation, Cf)
            
            # Centroid of triangle in image coordinates
            Ci = (Pz1 + Pz2 + Pz3) / 3.0
            
            # Displacement of frame in image coordinates
            Zposition = Ci - Cfi
            if abs(Zposition[2]) > 20.0:
                print("Registration::LocalizeFrame - Displacement too large, something is wrong.")
                return None, None
            
            print(f"Displacement [mm]: [{Zposition[0]}, {Zposition[1]}, {Zposition[2]}]")
            
            return Zposition, Zorientation
        # 9 fiducial version
        elif self.numFiducials == 9:
            # --- Compute diagonal points in the z-frame coordinates ---
            # SIDE 1
            Pz1 = make_vector(Zcoordinates[0][0], Zcoordinates[0][1])
            Pz2 = make_vector(Zcoordinates[1][0], Zcoordinates[1][1])
            Pz3 = make_vector(Zcoordinates[2][0], Zcoordinates[2][1])
            
            # Origin and direction vector of diagonal fiducial
            Oz = make_vector(*self.frameTopology[0])
            Vz = make_vector(*self.frameTopology[3])
            
            # Solve for the diagonal intercept in Z-frame coordinates
            # Assume distance between parallel fiducials is self.frameTopology[0][1]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[0][1]*2)
            P2f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P2f is None:
                return None, None
            
            # BASE
            Pz1 = make_vector(Zcoordinates[3][0], Zcoordinates[3][1])
            Pz2 = make_vector(Zcoordinates[4][0], Zcoordinates[4][1])
            Pz3 = make_vector(Zcoordinates[5][0], Zcoordinates[5][1])
            
            Oz = make_vector(*self.frameTopology[1])
            Vz = make_vector(*self.frameTopology[4])
            
            # Assume distance between parallel fiducials is self.frameTopology[1][0]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[1][0]*2)
            P4f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P4f is None:
                return None, None
            
            # SIDE 2
            Pz1 = make_vector(Zcoordinates[6][0], Zcoordinates[6][1])
            Pz2 = make_vector(Zcoordinates[7][0], Zcoordinates[7][1])
            Pz3 = make_vector(Zcoordinates[8][0], Zcoordinates[8][1])
            
            Oz = make_vector(*self.frameTopology[2])
            Vz = make_vector(*self.frameTopology[5])
            
            # Assume distance between parallel fiducials is self.frameTopology[2][1]*2
            # TODO: Perhaps the distance should be a parameter?
            fiducialDistance = np.abs(self.frameTopology[2][1]*2)
            P6f = self.SolveZ(Pz1, Pz2, Pz3, Oz, Vz, fiducialDistance)
            if P6f is None:
                return None, None
            
            # --- Compute Transformation Between Image and Frame ---
            # Compute z-frame cross section coordinate frame
            Vx = P2f - P6f
            Vy = P4f - P6f
            
            # Normalize Vx first
            Vx_norm = np.linalg.norm(Vx)
            if Vx_norm < self.MEPSILON:
                print("Registration::LocalizeFrame - Vx is too small, something is wrong.")
                return None, None
            Vx = Vx / Vx_norm
            
            # Compute Vz using normalized Vx
            Vz = np.cross(Vx, Vy)
            Vz_norm = np.linalg.norm(Vz)
            if Vz_norm < self.MEPSILON:
                print("Registration::LocalizeFrame - Vz is too small, something is wrong.")
                return None, None
            Vz = Vz / Vz_norm
            
            # Recompute Vy to ensure perfect orthogonality
            Vy = np.cross(Vz, Vx)
            
            # Create rotation matrix and convert to quaternion
            rotation_matrix = np.column_stack((Vx, Vy, Vz))
            transform_matrix = np.eye(4)
            transform_matrix[:3, :3] = rotation_matrix
            Qft = zf.MatrixToQuaternion(transform_matrix)
            
            # Check that the fiducial in the center of the top row is sufficiently centered
            if abs(Zcoordinates[4][0]) > 10:
                print("Registration::LocalizeFrame - Center & uppermost fiducial is not sufficiently centered along the x-axis")
                return None, None
            
            # Compute image cross-section coordinate frame
            Pz1 = make_vector(Zcoordinates[1][0], Zcoordinates[1][1])
            Pz2 = make_vector(Zcoordinates[4][0], Zcoordinates[4][1])
            Pz3 = make_vector(Zcoordinates[7][0], Zcoordinates[7][1])
            
            Vx = Pz1 - Pz3
            Vy = Pz2 - Pz3
            Vz = np.cross(Vx, Vy)
            Vy = np.cross(Vz, Vx)

            Vx_norm = np.linalg.norm(Vx)
            Vy_norm = np.linalg.norm(Vy)
            Vz_norm = np.linalg.norm(Vz)

            if Vx_norm < self.MEPSILON or Vy_norm < self.MEPSILON or Vz_norm < self.MEPSILON:
                print("Registration::LocalizeFrame - Vx, Vy, or Vz is too small, something is wrong.")
                return None, None
            
            # Normalize vectors
            Vx = Vx / Vx_norm
            Vy = Vy / Vy_norm
            Vz = Vz / Vz_norm
            
            # Create rotation matrix and convert to quaternion
            rotation_matrix = np.column_stack((Vx, Vy, Vz))
            transform_matrix = np.eye(4)
            transform_matrix[:3, :3] = rotation_matrix
            Qit = zf.MatrixToQuaternion(transform_matrix)
            
            # Compute rotation between frame and image
            Zorientation = zf.QuaternionDivide(Qit, Qft)
            
            # Check rotation angle
            angle = 2 * np.arccos(Zorientation[3])  # w component
            if abs(angle) > 15.0:
                print("Registration::LocalizeFrame - Rotation angle too large, something is wrong.")
                return None, None
            
            # Compute axis of rotation
            if angle == 0.0:
                axis = np.array([1.0, 0.0, 0.0])
            else:
                denom = np.sqrt(1 - Zorientation[3] * Zorientation[3])
                if abs(denom) < self.MEPSILON:
                    print("Registration::LocalizeFrame - Division by zero in axis calculation.")
                    return None, None
                axis = Zorientation[:3] / denom
                axis = axis / np.linalg.norm(axis)
            
            print(f"Rotation Angle [degrees]: {angle * 180.0 / np.pi}")
            print(f"Rotation Axis: [{axis[0]}, {axis[1]}, {axis[2]}]")
            
            # Compute translational component
            Cf = (P2f + P4f + P6f) / 3.0
            Cfi = zf.QuaternionRotateVector(Zorientation, Cf)
            Ci = (Pz1 + Pz2 + Pz3) / 3.0
            
            # Displacement of frame in image coordinates
            Zposition = Ci - Cfi
            if abs(Zposition[2]) > 20.0:
                print("Registration::LocalizeFrame - Displacement too large, something is wrong.")
                return None, None
            
            print(f"Displacement [mm]: [{Zposition[0]}, {Zposition[1]}, {Zposition[2]}]")
            
            return Zposition, Zorientation

    def SolveZ(self, P1, P2, P3, Oz, Vz, fiducialDistance):
        """Find the point at which the diagonal line fiducial is intercepted.
        
        Uses the three intercepts for a single set of planar line fiducials
        contained in one side of the Z-frame.
        
        Args:
            P1 (numpy.ndarray): Intercept point of first line fiducial in image
            P2 (numpy.ndarray): Intercept point of second line fiducial in image
            P3 (numpy.ndarray): Intercept point of third line fiducial in image
            Oz (numpy.ndarray): Origin of this side of the Z-frame, in Z-frame coordinates
            Vz (numpy.ndarray): Vector representing orientation of this side of Z-frame
            fiducialDistance (float): Distance between parallel fiducials (used to calculate diagonal length)
            
        Returns:
            numpy.ndarray: Diagonal intercept in physical Z-frame coordinates (P2f),
                        or None if computation fails
        """
        try:
            # Normalize the direction vector of the diagonal fiducial
            Vz = Vz / np.linalg.norm(Vz)
            
            # Compute distances between points
            D12 = np.linalg.norm(P1 - P2)
            D23 = np.linalg.norm(P2 - P3)
            
            if D12 + D23 < self.MEPSILON:
                print("Registration::SolveZ - Division by zero in distance calculation.")
                return None
                
            # Length of diagonal - Diagonal distance between parallel fiducials
            Ld = fiducialDistance * np.sqrt(2.0)
            
            # Compute intercept length
            Lc = Ld * D23 / (D12 + D23)
            
            # Compute P2 in frame coordinates
            P2f = Oz + Vz * Lc
            
            return P2f
            
        except Exception as e:
            print(f"Registration::SolveZ - Error in computation: {str(e)}")
            return None
        
    def FindMax(self, matrix):
        """Find the maximum value in a matrix and its coordinates.
        
        Searches for the maximum value while avoiding a 10-pixel margin around the edges
        to avoid image artifacts.
        
        Args:
            matrix (numpy.ndarray): The input matrix
            
        Returns:
            tuple: (max_value, [row, col]) where:
                - max_value is the maximum value found in the matrix
                - [row, col] are the coordinates where the maximum occurs
        """
        # Get matrix dimensions
        rows, cols = matrix.shape
        
        # Initialize max value and coordinates
        max_val = 0
        max_coords = [0, 0]
        
        # Avoid 10-pixel margin due to image artifacts
        for i in range(10, rows-10):
            for j in range(10, cols-10):
                if max_val < matrix[i, j]:
                    max_val = matrix[i, j]
                    max_coords = [i, j]
        
        return max_val, max_coords