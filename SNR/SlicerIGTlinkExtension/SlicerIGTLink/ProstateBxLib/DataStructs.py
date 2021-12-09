# Data structures used for prostate biopsy navigation
import numpy

class TargetMarker:
  """Represent one target marker
  """
  def __init__(self, depth=0, pos=[0.0, 0.0, 0.0]):
    self.depth = depth
    self.pos = pos
  def __str__(self):
    return "depth: %.3f pos: [%.3f, %.3f, %.3f]"%(self.depth, self.pos[0], self.pos[1], self.pos[2])

class SheetHole:
  """Represents one hole in the guide sheet
  """
  def __init__(self, x=0.0, y=0.0, depth=0.0, normal=[1.0,1.0,1.0]):
    self.x=x
    self.y=y
    self.depth=depth
    self.normal=normal
  def __str__(self):
    return "Sheet hole x=%.3f y=%.3f z=%.3f"%(self.x, self.y, self.depth)

class CalibrationMarker:
  """MRI Visible frame markers have position and orientation.
     Orientation is normalized.
  """
  # Beekley MR_SPOT markers have two lengths, we usually use the long one. These numbers
  # define the max length of of the volume rendered markers detected on the frame scan 
  MR_SPOT_SHORT = 15.0
  MR_SPOT_LONG = 30.0
  # To verify registration, we display cylinders through the defined and transformed marker
  # positions at the given orientation. The tubes need to be longer than the markers in case
  # of perfect alignment. The scale factor is applied to the spot length to get the frame length
  MARKER_SCALE = 2.0
  CALIBRATOR_LENGTH = MR_SPOT_LONG * MARKER_SCALE
  def __init__(self, pos=[0.0,0.0,0.0], orientation=[0.0, 0.0, 0.0], flen=CALIBRATOR_LENGTH):
    # print 'orientation = ', orientation, ', flen = ', flen
    self.pos = pos
    norm = numpy.linalg.norm(orientation)
    if norm == 0:
      self.orientation = orientation
    else:
      self.orientation = orientation / norm
    self.flen = flen

  def __str__(self):
    return "pos=%s orientation=%s length=%d"%(self.pos, self.orientation, self.flen)

  def calcPos(self, flen):
    '''Calculate a point on the line through the marker position, using pos as the origin.
    '''
    offset = [x * flen for x in self.orientation]
    pt = [0.0, 0.0, 0.0]
    for i in range(len(self.pos)):
      pt[i] = self.pos[i] + offset[i]
    return pt

  # A tube through the marker is defined by a line from pos0 through pos to pos2, total
  # length flen.
  def pos0(self):
    '''Calculate a point before the marker position along the orientation vector
    by subtracting half the length.
    '''
    return self.calcPos(-(self.flen/2.0))

  def pos2(self):
    '''Calculate a point after the marker position along the orientation vctor
    by adding half the length.
    '''
    return self.calcPos(self.flen/2.0)
