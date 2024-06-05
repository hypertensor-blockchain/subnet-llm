import torch

# PUBLIC_INITIAL_PEERS = [
#     # IPv4 DNS addresses
#     "/dns/bootstrap1.petals.dev/tcp/31337/p2p/QmedTaZXmULqwspJXz44SsPZyTNKxhnnFvYRajfH7MGhCY",
#     "/dns/bootstrap2.petals.dev/tcp/31338/p2p/QmQGTqmM7NKjV6ggU1ZCap8zWiyKR89RViDXiqehSiCpY5",
#     # IPv6 DNS addresses
#     "/dns6/bootstrap1.petals.dev/tcp/31337/p2p/QmedTaZXmULqwspJXz44SsPZyTNKxhnnFvYRajfH7MGhCY",
#     "/dns6/bootstrap2.petals.dev/tcp/31338/p2p/QmQGTqmM7NKjV6ggU1ZCap8zWiyKR89RViDXiqehSiCpY5",
#     # Reserved IPs
#     "/ip4/159.89.214.152/tcp/31337/p2p/QmedTaZXmULqwspJXz44SsPZyTNKxhnnFvYRajfH7MGhCY",
#     "/ip4/159.203.156.48/tcp/31338/p2p/QmQGTqmM7NKjV6ggU1ZCap8zWiyKR89RViDXiqehSiCpY5",
# ] 

# PUBLIC_INITIAL_PEERS = [
#     "/ip4/18.118.105.117/tcp/31330/p2p/12D3KooWEsgrFiS8Kr2tLBkBzAKRQjRJfz7urjBRoXSrJ99QoWPq",
#     "/ip4/18.118.105.117/udp/31330/quic/p2p/12D3KooWEsgrFiS8Kr2tLBkBzAKRQjRJfz7urjBRoXSrJ99QoWPq"
# ]

PUBLIC_INITIAL_PEERS = [
    "/ip4/170.250.110.241/tcp/31330/p2p/12D3KooWAYAAtfNx8Pg8DX1UL5P1na2QWzyzSYMS7TD7NuidhMCK", 
    "/ip4/170.250.110.241/udp/31330/quic/p2p/12D3KooWAYAAtfNx8Pg8DX1UL5P1na2QWzyzSYMS7TD7NuidhMCK"
]


# The reachability API is currently used only when connecting to the public swarm
# REACHABILITY_API_URL = "https://health.petals.dev"
REACHABILITY_API_URL = "https://dashboard.hypertensor.org"

DTYPE_MAP = dict(bfloat16=torch.bfloat16, float16=torch.float16, float32=torch.float32, auto="auto")
