import sys
import os
import struct
import lzma
import zlib
import crcmod
import argparse

COMPRESS_GZIP  = 0
COMPRESS_LZMA  = 1
COMPRESSION  = COMPRESS_LZMA
MAGIC        = b"TiMOS\x00\x00\x00"
BUILD_REV    = b"B-7.0.R7"
BUILD_STRING = b"Tue Jun 30 14:16:14 IST 2015 by builder in /home/builder/7.0B1/R7/panos/main"
NULL16       = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
NULL8        = b"\x00\x00\x00\x00\x00\x00\x00\x00"
FORMAT_TYPE  = b"1"
NUM_SEGMENTS = 2
TEXT_ENTRY   = 0x0100000
TEXT_BASE    = 0x0100000
DATA_ENTRY   = 0x0000000
DATA_BASE    = 0x6643000

def auto_int(x):
    return int(x, 0)

def pack(outfile, textfile, datafile):
	outfd  = open(outfile, 'wb')
	textfd = open(textfile, 'rb')
	datafd = open(datafile, 'rb')

	outfd.write(MAGIC)
	outfd.write(BUILD_REV)
	outfd.write(NULL16)
	outfd.write(NULL16)
	outfd.write(BUILD_STRING)
	mod16 = len(BUILD_STRING) % 16
	if mod16 != 0:
		outfd.write(b"\x00" * (16 - mod16))
	format_type = b"1"
	if COMPRESSION == COMPRESS_LZMA:
		format_type = b"11"
	outfd.write(format_type)
	outfd.write(b"\x00" * (0x10 - len(format_type)))
	outfd.write(NULL16)
	outfd.write(NULL8)
	outfd.write(b"\x00\x00\x00\x07\x00\x00\x00\x06") # ???

	outfd.write(b"\x00\x00\x00") 
	outfd.write(struct.pack("B", NUM_SEGMENTS))

	print("[+] reading text '%s'" % textfile)
	text_blob = textfd.read()

	print("[+] reading data '%s'" % datafile)
	data_blob = datafd.read()

	crc = crcmod.predefined.mkCrcFun("jamcrc")

	print("[+] calculating jamcrc (text)")
	text_crc = crc(text_blob)
	print("[i] got text section crc          0x%08x" % text_crc)
	print("[+] calculating jamcrc (data)")
	
	data_crc = crc(data_blob)
	print("[i] got data section crc          0x%08x" % data_crc)
	text_zipped = b""
	data_zipped = b""
	text_uncompressed_len = len(text_blob)
	data_uncompressed_len = len(data_blob)
	if COMPRESSION == COMPRESS_GZIP:
		print("[+] zlib compression (text)")
		compress_obj          = zlib.compressobj(level=-1, wbits=15, memLevel=8, strategy=zlib.Z_DEFAULT_STRATEGY)
		text_zipped           = ( b"\x08" + compress_obj.compress(text_blob) + compress_obj.flush() )
		print("[+] zlib compression (data)")
		compress_obj          = zlib.compressobj(level=-1, wbits=15, memLevel=8, strategy=zlib.Z_DEFAULT_STRATEGY)
		data_zipped           = ( b"\x08" + compress_obj.compress(data_blob) + compress_obj.flush() )
	else:
		print("[+] lzma compression (text)")
		text_zipped 		  = lzma.compress(text_blob, format=lzma.FORMAT_ALONE)
		print("[+] lzma compression (data)")
		data_zipped 		  = lzma.compress(data_blob, format=lzma.FORMAT_ALONE)


	text_zipped_len       = len(text_zipped) 
	data_zipped_len       = len(data_zipped) 
	print("[i] text zip size                 0x%08x" % text_zipped_len)
	print("[i] data zip size                 0x%08x" % data_zipped_len)

	print("[+] calculating jamcrc compressed (text)")
	text_zip_crc = crc(text_zipped)
	print("[i] got text section crc (zip)    0x%08x" % text_zip_crc)

	print("[+] calculating jamcrc compressed (data)")
	data_zip_crc = crc(data_zipped)
	print("[i] got data section crc (zip)    0x%08x" % data_zip_crc)
	print("[+] reticulating splines...")
	text_offset           = 0x400
	text_zip_end 		  = 0x400 + text_zipped_len
	text_zip_pad          = 0x00
	if (text_zip_end % 16) != 0:
		text_zip_pad += (16 - (text_zip_end % 16))
	text_zip_pad += 16

	data_offset = text_zip_end + text_zip_pad

	print("[i] text offset                   0x%08x" % text_offset)
	print("[i] data offset                   0x%08x" % data_offset)	
	print("[i] text compress padding         0x%08x" % text_zip_pad)
	
	
	print("[+] finalising '%s'" % outfile)
	print("[+} writing header info")
	print("[i] text offset                   0x%08x" % text_offset)
	print("[i] data offset                   0x%08x" % data_offset)	
	outfd.write(struct.pack("!12sIIIIII", b"text", text_offset, text_zipped_len, text_uncompressed_len, text_crc, TEXT_BASE, TEXT_ENTRY))
	outfd.write(struct.pack("!12sIIIIII", b"data", data_offset, data_zipped_len, data_uncompressed_len, data_crc, DATA_BASE, DATA_ENTRY))
	outfd.write(b"\x00" * (0x1d0 - outfd.tell()))
	outfd.write(b"\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x00") # ???
	#outfd.write(b"\x09\x3b\x97\x66")
	outfd.write(struct.pack("!I", text_zipped_len))
	#outfd.write(b"\x10\x49\x92\x62")
	outfd.write(struct.pack("!I", data_zipped_len))
	outfd.write(b"\x00" * (0x400 - outfd.tell()))
	
	outfd.close()
	outfd2 = open(outfile, "rb")
	print("[+] calculating header jamcrc")
	contents = outfd2.read()

	header_crc = crc(contents[0:0x400])
	print("[i] header crc                    0x%4x" % header_crc)
	outfd2.close()
	print("[+] writing header crc")
	outfd  = open(outfile, 'r+b')
	outfd.seek(0x1d8)
	outfd.write(struct.pack("!I", header_crc))
	outfd.seek(0x00, 2)
	print("[+] writing compressed text")
	outfd.write(text_zipped)
	outfd.write(b"\x00" * text_zip_pad)
	print("[+] writing compressed data")
	outfd.write(data_zipped)


	textfd.close()
	datafd.close()

	print("[!] done & dusted")

	
	
def main():
	global TEXT_BASE
	global TEXT_ENTRY
	global DATA_BASE

	print("SR/OS TiMOS Firmware Packer v0.01 - Caleb Anderson 2017")
	parser = argparse.ArgumentParser(description="pack SR/OS (TiMOS) firmware files")
	parser.add_argument("outfile",  help="file to write packed firmware to")
	parser.add_argument("textfile", help="file that contains text section")
	parser.add_argument("datafile", help="file that contains data section")
	parser.add_argument("-b", "--base",     type=auto_int, nargs='?',  const=TEXT_BASE,  help=('text base addr (0x%08x)' % TEXT_BASE))
	parser.add_argument("-e", "--entry",    type=auto_int, nargs='?',  const=TEXT_ENTRY, help=('text exec addr (0x%08x)' % TEXT_ENTRY))
	parser.add_argument("-d", "--dataload", type=auto_int, nargs='?',  const=DATA_BASE,  help=('data load addr (0x%08x)' % DATA_BASE))
	args = parser.parse_args()
	if args.base:
		TEXT_BASE  = args.base
	if args.entry:
		TEXT_ENTRY = args.entry
	if args.dataload:
		DATA_BASE  = args.dataload
	print("[?] text base:                    0x%08x" % TEXT_BASE)
	print("[?] text exec:                    0x%08x" % TEXT_ENTRY)
	print("[?] data load:                    0x%08x" % DATA_BASE)
	pack(args.outfile, args.textfile, args.datafile)

if __name__ == '__main__':
	main()
	




