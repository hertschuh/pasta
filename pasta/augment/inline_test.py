# coding=utf-8
"""Tests for augment.inline."""
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ast
import sys
import textwrap
import unittest

import pasta
from pasta.augment import inline
from pasta.base import test_utils

astlib = getattr(pasta, 'TEST_ASTLIB', ast)


class InlineTest(test_utils.TestCase):

  def test_inline_simple(self):
    src = 'x = 1\na = x\n'
    t = astlib.parse(src)
    inline.inline_name(t, 'x', astlib=astlib)
    self.checkAstsEqual(t, astlib.parse('a = 1\n'), astlib=astlib)

  def test_inline_multiple_targets(self):
    src = 'x = y = z = 1\na = x + y\n'
    t = astlib.parse(src)
    inline.inline_name(t, 'y', astlib=astlib)
    self.checkAstsEqual(t, astlib.parse('x = z = 1\na = x + 1\n'),
                        astlib=astlib)

  def test_inline_multiple_reads(self):
    src = textwrap.dedent("""\
        CONSTANT = "foo"
        def a(b=CONSTANT):
          return b == CONSTANT
        """)
    expected = textwrap.dedent("""\
        def a(b="foo"):
          return b == "foo"
        """)
    t = astlib.parse(src)
    inline.inline_name(t, 'CONSTANT', astlib=astlib)
    self.checkAstsEqual(t, astlib.parse(expected), astlib=astlib)

  def test_inline_non_constant_fails(self):
    src = textwrap.dedent("""\
        NOT_A_CONSTANT = "foo"
        NOT_A_CONSTANT += "bar"
        """)
    t = astlib.parse(src)
    with self.assertRaisesRegexp(inline.InlineError,
                                 '\'NOT_A_CONSTANT\' is not a constant'):
      inline.inline_name(t, 'NOT_A_CONSTANT', astlib=astlib)

  def test_inline_function_fails(self):
    src = 'def func(): pass\nfunc()\n'
    t = astlib.parse(src)

    with self.assertRaisesRegexp(
        inline.InlineError, '\'func\' is not a constant; it has type %r' %
        astlib.FunctionDef):
      inline.inline_name(t, 'func', astlib=astlib)

  def test_inline_conditional_fails(self):
    src = 'if define:\n  x = 1\na = x\n'
    t = astlib.parse(src)
    with self.assertRaisesRegexp(inline.InlineError,
                                 '\'x\' is not a top-level name'):
      inline.inline_name(t, 'x', astlib=astlib)

  def test_inline_non_assign_fails(self):
    src = 'CONSTANT1, CONSTANT2 = values'
    t = astlib.parse(src)
    with self.assertRaisesRegexp(
        inline.InlineError, '\'CONSTANT1\' is not declared in an assignment'):
      inline.inline_name(t, 'CONSTANT1', astlib=astlib)


if __name__ == '__main__':
  unittest.main()
