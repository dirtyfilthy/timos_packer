# SR/OS (TiMOS) Firmware Packer 2017

Firmware packer for the Alcatel-Lucent SR/OS (TiMOS) 7750 / 7210 SAS-K etc.

https://github.com/dirtyfilthy/timos_packer

## Dependencies

Requires python3

pip install crcmod

## Usage:

    python3 timos_packer.py -h
    
    SR/OS TiMOS Firmware Packer - Caleb Anderson
    usage: timos_packer.py [-h] [-b [BASE]] [-e [ENTRY]] [-d [DATALOAD]]
                           outfile textfile datafile
   
    pack SR/OS (TiMOS) firmware files
    
    positional arguments:
      outfile               file to write packed firmware to
      textfile              file that contains text section
      datafile              file that contains data section
    
    optional arguments:
      -h, --help            show this help message and exit
      -b [BASE], --base [BASE]
                            text base addr (0x00100000)
      -e [ENTRY], --entry [ENTRY]
                            text exec addr (0x00100000)
      -d [DATALOAD], --dataload [DATALOAD]
                            data load addr (0x06643000)

