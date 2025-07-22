#!/usr/bin/python3
import glob
import os
import re
import sys

def extract_sources(gni_file):
    with open(gni_file, 'r') as f:
        data = f.read()
    
    objs = {}
    matches = re.findall(r'\s*(\w+?)\s*=\s*\[\s*([\"\w\-\.\/\,\s]+?),?\s*\]\s*', data)
    for name, names in matches:
        srcs = re.findall(r'\"([\w\-\.]+)\",?\s*', names)
        objs[name] = srcs
    
    return objs

def get_src_files(path):
    name = os.path.split(path)[-1]
    gni_file = os.path.join(path, name+'_sources.gni')
    objs = extract_sources(gni_file)
    return objs[name+'_sources']

def get_default_src_files(gni_file):
    objs = extract_sources(gni_file)
    for key in objs.keys():
        if key.endswith('_cc_files'):
            return objs[key]

def get_src_from_path(path):
    srcs = glob.glob(os.path.join(path, '*.cc'))
    return srcs

# runtime directory
BASEDIR = sys.argv[1] if len(sys.argv) > 1 else '.'
os.chdir(BASEDIR)
BASEDIR = '.'

# check if BASEDIR contains runtime directory in case user input is dart sdk directory
tmpdir = os.path.join(BASEDIR, 'runtime')
if os.path.isdir(tmpdir):
    SDKDIR = BASEDIR
    BASEDIR = tmpdir
else:
    SDKDIR = os.path.join(BASEDIR, '..')

cc_srcs = []
hdrs = []
for path in ('vm', 'platform', 'vm/heap', 'vm/ffi', 'vm/regexp'):
    path = os.path.join(BASEDIR, path)
    if not os.path.isdir(path):
        print(f"Warning: Directory not found: {path}")
        continue
    try:
        srcs = get_src_files(path)
        #cc_srcs.extend([ os.path.join(path, src) for src in srcs if src.endswith('.cc') ])
        for src in srcs:
            src_path = os.path.join(path, src)
            if os.path.isfile(src_path):
                cc_srcs.append(src_path)
                if src.endswith('h'):
                    hdrs.append(src_path)
            else:
                print(f"Warning: Source file not found: {src_path}")
    except Exception as e:
        print(f"Warning: Failed to process directory {path}: {e}")
        continue

# extra source files
extra_files = ( 'vm/version.cc', 'vm/dart_api_impl.cc', 'vm/native_api_impl.cc',
        'vm/compiler/runtime_api.cc', 'vm/compiler/jit/compiler.cc', 'platform/no_tsan.cc')
for name in extra_files:
    file_path = os.path.join(BASEDIR, name)
    if os.path.isfile(file_path):
        cc_srcs.append(file_path)
    else:
        print(f"Warning: Extra source file not found: {file_path}")

# extra public header
hdrs.append(os.path.join(BASEDIR, 'vm/version.h'))

# other libraries
for lib in ('async', 'concurrent', 'core', 'developer', 'ffi', 'isolate', 'math', 'typed_data', 'vmservice', 'internal'):
    gni_file = os.path.join(BASEDIR, 'lib', lib+'_sources.gni')
    if os.path.isfile(gni_file):
        try:
            srcs = get_default_src_files(gni_file)
            if srcs:
                for src in srcs:
                    if src.endswith('.cc'):
                        src_path = os.path.join(BASEDIR, 'lib', src)
                        if os.path.isfile(src_path):
                            cc_srcs.append(src_path)
                        else:
                            print(f"Warning: Library source file not found: {src_path}")
        except Exception as e:
            print(f"Warning: Failed to process library {lib}: {e}")
    else:
        print(f"Warning: Library gni file not found: {gni_file}")

double_conversion_dir = BASEDIR+'/third_party/double-conversion/src'
if not os.path.isdir(double_conversion_dir):
    double_conversion_dir = SDKDIR+'/third_party/double-conversion/src'
    assert os.path.isdir(double_conversion_dir)
cc_srcs.extend(get_src_from_path(double_conversion_dir))

#print('VMSRCS='+' '.join(cc_srcs))
#print(' '.join(cc_srcs))
#with open('sources.list', 'w') as f:
#    f.write('\n'.join(cc_srcs))

# CMake file need forward slash in path even in Windows
if os.sep == '\\':
    cc_srcs = [ src.replace(os.sep, '/') for src in cc_srcs ]
    hdrs = [ src.replace(os.sep, '/') for src in hdrs ]

# Check if we have any source files
if not cc_srcs:
    print("Error: No source files found! This will cause CMake to fail.")
    print("Please check if the Dart SDK was properly downloaded and the directory structure is correct.")
    sys.exit(1)

print(f"Found {len(cc_srcs)} source files")

with open('sourcelist.cmake', 'w') as f:
    f.write('set(SRCS \n    ')
    f.write('\n    '.join(cc_srcs))
    f.write('\n)\n')
    
    #f.write('\n')
    #f.write('set(PUB_HDRS \n    ')
    #f.write('\n    '.join(hdrs))
    #f.write('\n)\n')