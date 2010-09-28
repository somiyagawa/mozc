# -*- coding: utf-8 -*-
# Copyright 2010, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
 The tool for generating zip code dictionary.
 Input files are shift-jis csv.
 Output lines will be printed as utf-8.

 usage:
 ./gen_zip_code_seed.py --zip_code=zip_code.csv --jigyosyo=jigyosyo.csv > zip_code_seed.tsv

 Zip code sample input line:
 01101,"060  ","0600007","ﾎｯｶｲﾄﾞｳ","ｻｯﾎﾟﾛｼﾁｭｳｵｳｸ","ｷﾀ7ｼﾞｮｳﾆｼ","北海道","札幌市中央区","北七条西",0

 Jigyosyo zip code sample input line:
 01101,"ｻﾂﾎﾟﾛｼﾁﾕｳｵｳｸﾔｸｼﾖ","札幌市中央区役所","北海道","札幌市中央区","南三条西","１１丁目","0608612","060  ","札幌",0,0,0
"""

__author__ = "toshiyuki"

import codecs
import optparse
import re
import sys
import unicodedata

class ZipEntry:
  def __init__(self, zip_code, level1, level2, level3, level4, allow_multiple):
    self.allow_multiple = allow_multiple

    # XXX-XXXX format
    self.zip_code = '-'.join([zip_code[0:3], zip_code[3:]])

    # When a postal code corresponds to multiple area, we don't use individual
    # area name.
    if (level3.find(u'以下に掲載がない場合') != -1 or
        level3.find(u'、') != -1):
      level3 = ''

    # We ignore additional information here.
    level3 = re.sub(u'（.*', u'', level3)

    # Normalize business name.
    level4 = re.sub(u'　', u' ', level4)

    address = u''.join([level1, level2, level3])
    if level4:
      address = u' '.join([address, level4])

    # Normalize character width.
    address = unicodedata.normalize('NFKC', address)
    self.address = address


def TrimColumnContent(column):
  """Returns column content without '\"'."""
  return column.strip('"')


def GetColumns(line):
  """Returns columns contents in list."""
  line = line.strip()
  columns = line.split(',')
  return map(TrimColumnContent, columns)


def ReadZipEntry(line):
  """Read zip code entry."""
  columns = GetColumns(line)
  zip_entry = ZipEntry(columns[2], columns[6], columns[7], columns[8], '',
                       (columns[12] == '1'))
  return zip_entry


def ReadJigyosyoEntry(line):
  """Read jigyosyo zip code entry."""
  columns = GetColumns(line)
  jigyosyo_entry = ZipEntry(columns[7], columns[3], columns[4], columns[5],
                       columns[2], False)
  return jigyosyo_entry


def PrintEntry(entry):
  """Print zip code entry."""
  zip_code = entry.zip_code
  address = entry.address
  line = '\t'.join([zip_code, address, '0'])
  print line.encode('utf-8')


def ParseOptions():
  """Parse command line options."""
  parser = optparse.OptionParser(usage='Usage: %prog [options]')
  parser.add_option('--zip_code', dest='zip_code',
                    action='store', default='',
                    help='specify zip code csv file path.')
  parser.add_option('--jigyosyo', dest='jigyosyo',
                    action='store', default='',
                    help='specify zip code csv file path.')
  (options, unused_args) = parser.parse_args()
  return options


def main():
  options = ParseOptions()
  header = '# zip code dictionary seed generated by %s' % __file__
  print header.encode('utf-8')

  seen = set()
  if options.zip_code:
    for line in codecs.open(options.zip_code, 'r', 'shift_jis',
                            errors='replace'):
      entry = ReadZipEntry(line)
      if (entry.zip_code in seen and
          not entry.allow_multiple):
        # Single entry may be recorded as multiple lines.
        # Here, simply discard them.

        # TODO(toshiyuki): Support multiple address entry.
        # for example,
        # 440-0032, "愛知県","豊橋市","岩田町居村、北郷中"
        # should be
        # 440-0032, "愛知県豊橋市岩田町居村" and
        # 440-0032, "愛知県豊橋市北郷中".
        continue
      PrintEntry(entry)
      seen.add(entry.zip_code)
  if options.jigyosyo:
    for line in codecs.open(options.jigyosyo, 'r', 'shift_jis',
                            errors='replace'):
      entry = ReadJigyosyoEntry(line)
      PrintEntry(entry)
  return 0


if __name__ == '__main__':
  sys.exit(main())