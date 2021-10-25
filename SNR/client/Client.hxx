#include <string>
#include <cstring>
#include <eigen3/Eigen/Dense>
#include <vector>

#include "igtlOSUtil.h"
#include "igtlMessageHeader.h"
#include "igtlTransformMessage.h"
#include "igtlImageMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlPositionMessage.h"

#if OpenIGTLink_PROTOCOL_VERSION >= 2
// #include "igtlPointMessage.h"
// #include "igtlTrajectoryMessage.h"
#include "igtlStringMessage.h"
// #include "igtlBindMessage.h"
// #include "igtlCapabilityMessage.h"
#endif // OpenIGTLink_PROTOCOL_VERSION >= 2

class Client
{
public:
    Client(char* hostname, int port){};
    // Member variables
    int _clientSocketConnected;
    std::string status;
    igtl::Socket::Pointer socket;
    char* _hostname;
    int _port;
    std::string start_up_status;
    std::string cached_start_up_status;

    //================ Public Methods ==============
    // This method receives data to the controller via OpenIGTLink
    static void *ThreadIGT(void *);

    // This method sends data out from the controller via OpenIGTLink, given some change in robot state
    void Sync();

    // This method disconnect the current socket
    void DisconnectSocket();

    // Methods got Receiving various IGT Data Types
    // int ReceiveStatus(igtl::Socket *socket, igtl::MessageHeader *header);
    std::string ReceiveString(igtl::Socket *socket, igtl::MessageHeader *header);
    // Eigen::Matrix4d ReceiveTransform(igtl::Socket *socket, igtl::MessageHeader *header);
    // std::vector<int> ReceiveArray(igtl::Socket *socket, igtl::MessageHeader *header);
};