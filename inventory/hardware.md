# Hardware Inventory

## CPU
 Architecture:                            x86_64
 CPU op-mode(s):                          32-bit, 64-bit
 Address sizes:                           39 bits physical, 48 bits virtual
 Byte Order:                              Little Endian
 CPU(s):                                  12
 On-line CPU(s) list:                     0-11
 Vendor ID:                               GenuineIntel
 Model name:                              Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz
 CPU family:                              6
 Model:                                   165
 Thread(s) per core:                      2
 Core(s) per socket:                      6
 Socket(s):                               1
 Stepping:                                2
 CPU max MHz:                             5000.0000
 CPU min MHz:                             800.0000
 BogoMIPS:                                5199.98
 Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust sgx bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp vnmi pku ospke sgx_lc md_clear flush_l1d arch_capabilities ibpb_exit_to_user
 Virtualization:                          VT-x
 L1d cache:                               192 KiB (6 instances)
 L1i cache:                               192 KiB (6 instances)
 L2 cache:                                1.5 MiB (6 instances)
 L3 cache:                                12 MiB (1 instance)
 NUMA node(s):                            1
 NUMA node0 CPU(s):                       0-11
 Vulnerability Gather data sampling:      Mitigation; Microcode
 Vulnerability Indirect target selection: Mitigation; Aligned branch/return thunks
 Vulnerability Itlb multihit:             KVM: Mitigation: VMX disabled
 Vulnerability L1tf:                      Not affected
 Vulnerability Mds:                       Not affected
 Vulnerability Meltdown:                  Not affected
 Vulnerability Mmio stale data:           Mitigation; Clear CPU buffers; SMT vulnerable
 Vulnerability Reg file data sampling:    Not affected
 Vulnerability Retbleed:                  Mitigation; Enhanced IBRS
 Vulnerability Spec rstack overflow:      Not affected
 Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
 Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
 Vulnerability Spectre v2:                Mitigation; Enhanced / Automatic IBRS; IBPB conditional; PBRSB-eIBRS SW sequence; BHI SW loop, KVM SW loop
 Vulnerability Srbds:                     Mitigation; Microcode
 Vulnerability Tsa:                       Not affected
 Vulnerability Tsx async abort:           Not affected
 Vulnerability Vmscape:                   Mitigation; IBPB before exit to userspace

## Memory
               total        used        free      shared  buff/cache   available
Mem:            15Gi       2.1Gi       9.9Gi       1.2Gi       3.3Gi        11Gi
Swap:             0B          0B          0B

## Block Devices
NAME        FSTYPE          FSVER  LABEL UUID                                 FSAVAIL FSUSE% MOUNTPOINTS
loop0       squashfs        4.0                                                     0   100% /snap/bare/5
loop1       squashfs        4.0                                                     0   100% /snap/core22/2216
loop2       squashfs        4.0                                                     0   100% /snap/core22/2292
loop3       squashfs        4.0                                                     0   100% /snap/core24/1643
loop4       squashfs        4.0                                                     0   100% /snap/firefox/7901
loop5       squashfs        4.0                                                     0   100% /snap/firefox/7967
loop6       squashfs        4.0                                                     0   100% /snap/gnome-42-2204/202
loop7       squashfs        4.0                                                     0   100% /snap/gnome-42-2204/247
loop8       squashfs        4.0                                                     0   100% /snap/gnome-46-2404/153
loop9       squashfs        4.0                                                     0   100% /snap/gtk-common-themes/1535
loop10      squashfs        4.0                                                     0   100% /snap/mesa-2404/1165
loop11      squashfs        4.0                                                     0   100% /snap/pycharm/83
loop12      squashfs        4.0                                                     0   100% /snap/pycharm/89
loop13      squashfs        4.0                                                     0   100% /snap/snap-store/1113
loop14      squashfs        4.0                                                     0   100% /snap/snap-store/1216
loop15      squashfs        4.0                                                     0   100% /snap/snapd/26865
loop16      squashfs        4.0                                                     0   100% /snap/snapd/27406
loop17      squashfs        4.0                                                     0   100% /snap/snapd-desktop-integration/343
loop18      squashfs        4.0                                                     0   100% /snap/snapd-desktop-integration/361
nvme1n1                                                                                      
├─nvme1n1p1 vfat            FAT32        04A6-A9CF                              40.2M    13% /boot/efi
├─nvme1n1p2 ext4            1.0          062eb807-6d30-4704-b16e-afa54065ece9   40.4G    21% /
├─nvme1n1p3 ext4            1.0          58adf88e-2e78-4236-821a-7efee7c924c2  145.1G    31% /home
├─nvme1n1p4 ext4            1.0          00dbd999-1413-4c9a-84a3-18848a07154f    7.1G    55% /var
├─nvme1n1p5 ext4            1.0          4a17d6cf-a44b-4b80-8577-fb5c5c6a4f2b   17.2G     0% /tmp
├─nvme1n1p6 ext4            1.0          e2d71dfe-d0f6-44bd-8159-c3281436a999   25.9G     0% /data
└─nvme1n1p7 ext4            1.0          048bea95-d970-41ad-951b-ed14039180f7   45.9M    80% /boot
nvme0n1     isw_raid_member 1.4.01                                                           
