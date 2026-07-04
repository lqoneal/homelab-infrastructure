# Network Inventory

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: wlo1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether 3c:58:c2:b2:91:61 brd ff:ff:ff:ff:ff:ff
    altname wlp0s20f3
    inet 10.0.0.35/24 brd 10.0.0.255 scope global dynamic noprefixroute wlo1
       valid_lft 172691sec preferred_lft 172691sec
    inet6 2601:601:9080:ba30::207/128 scope global dynamic noprefixroute 
       valid_lft 67873sec preferred_lft 67873sec
    inet6 2601:601:9080:ba30:8cb3:8cf3:ea5a:16e8/64 scope global temporary dynamic 
       valid_lft 67981sec preferred_lft 67981sec
    inet6 2601:601:9080:ba30:e1b1:8dff:6669:c088/64 scope global dynamic mngtmpaddr noprefixroute 
       valid_lft 67981sec preferred_lft 67981sec
    inet6 fe80::a663:4587:2377:6688/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether 9a:36:79:26:7f:a0 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever

## Routes
default via 10.0.0.1 dev wlo1 proto dhcp metric 600 
10.0.0.0/24 dev wlo1 proto kernel scope link src 10.0.0.35 metric 600 
169.254.0.0/16 dev wlo1 scope link metric 1000 
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown 
