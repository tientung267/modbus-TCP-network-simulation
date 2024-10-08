SOCKET_TIMEOUTS = 1.1
NUM_CLIENT = 1
NUM_REG_TO_READ = 1
FUNCTION_CODE = 3
S1_STEG_MESS = "this steganography message will be embedded with S1 method"
T1_STEG_MESS = "this steganography message will be embedded with T1 method"
SLEEP_DURATION = 1
NUM_BITS_CHARACTER = 7  # each character in hidden message is represented by 7 bits (number in ASCII table)
NUM_BITS_HEADER = 10  # 10 first bits in embedded message represents number of bits following (max 1023 bits)
CACHE_TTL = 30  # Time-to-live of a cached value in the cache
DELAY_INTERVAL = 30  # Time in seconds after which delay should be introduced
DELAY_DURATION = 10  # Time in seconds indicates how long the throttling of the network should take place
NETWORK_THROTTLING_INTERVAL = 30  # Time in seconds after which no steganography delay should be applied
NETWORK_THROTTLING_DURATION = 10  # After network throttling period, steganography delay can be applied again
DUMMY_EMBEDDED_BYTE = 0
