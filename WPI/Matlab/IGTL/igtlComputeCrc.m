% Computes 64-bit CRC check sum according to ECMA-182 standard.
function crc64_result = igtlComputeCrc(dataBuffer)
    crc64_result = igtlComputeCrc_2018(dataBuffer);
    %crc64_result = igtlComputeCrc_2024(dataBuffer);
end