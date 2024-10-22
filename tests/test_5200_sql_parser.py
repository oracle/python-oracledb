# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

"""
5200 - Module for testing the SQL parser.
"""

import unittest

import test_env


class TestCase(test_env.BaseTestCase):
    def test_5200(self):
        "5200 - single line comment"
        self.cursor.prepare(
            "--begin :value2 := :a + :b + :c +:a +3; end;\n"
            "begin :value2 := :a + :c +3; end; -- not a :bind_variable"
        )
        self.assertEqual(self.cursor.bindnames(), ["VALUE2", "A", "C"])

    def test_5201(self):
        "5201 - multiple line comment"
        self.cursor.prepare(
            "/*--select * from :a where :a = 1\n"
            "select * from table_names where :a = 1*/\n"
            "select :table_name, :value from dual"
        )
        self.assertEqual(self.cursor.bindnames(), ["TABLE_NAME", "VALUE"])

    def test_5202(self):
        "5202 - constant strings"
        statement = """
                    begin
                        :value := to_date('20021231 12:31:00', :format);
                    end;"""
        self.cursor.prepare(statement)
        self.assertEqual(self.cursor.bindnames(), ["VALUE", "FORMAT"])

    def test_5203(self):
        "5203 - multiple division operators"
        self.cursor.prepare(
            """
            select :a / :b, :c / :d
            from dual
            """
        )
        self.assertEqual(self.cursor.bindnames(), ["A", "B", "C", "D"])

    def test_5204(self):
        "5204 - starting with parentheses"
        sql = "(select :a from dual) union (select :b from dual)"
        self.cursor.prepare(sql)
        self.assertEqual(self.cursor.bindnames(), ["A", "B"])

    def test_5205(self):
        "5205 - invalid quoted bind"
        sql = 'select ":test", :a from dual'
        self.cursor.prepare(sql)
        self.assertEqual(self.cursor.bindnames(), ["A"])

    def test_5206(self):
        "5206 - non-ascii character in the bind name"
        sql = "select :méil$ from dual"
        self.cursor.prepare(sql)
        self.assertEqual(self.cursor.bindnames(), ["MÉIL$"])

    def test_5207(self):
        "5207 - various quoted bind names"
        tests = [
            ('select :"percent%" from dual', ["percent%"]),
            ('select : "q?marks" from dual', ["q?marks"]),
            ('select :"percent%(ens)yah" from dual', ["percent%(ens)yah"]),
            ('select :  "per % cent" from dual', ["per % cent"]),
            ('select :"per cent" from dual', ["per cent"]),
            ('select :"par(ens)" from dual', ["par(ens)"]),
            ('select :"more/slashes" from dual', ["more/slashes"]),
            ('select :"%percent" from dual', ["%percent"]),
            ('select :"/slashes/" from dual', ["/slashes/"]),
            ('select :"1col:on" from dual', ["1col:on"]),
            ('select :"col:ons" from dual', ["col:ons"]),
            ('select :"more :: %colons%" from dual', ["more :: %colons%"]),
            ('select :"more/slashes" from dual', ["more/slashes"]),
            ('select :"spaces % spaces" from dual', ["spaces % spaces"]),
            ('select "col:nns", :"col:ons", :id from dual', ["col:ons", "ID"]),
        ]
        for sql, expected in tests:
            with self.subTest(sql=sql, expected=expected):
                self.cursor.prepare(sql)
                self.assertEqual(self.cursor.bindnames(), expected)

    def test_5208(self):
        "5208 - sql containing quoted identifiers and strings"
        sql = 'select "/*_value1" + : "VaLue_2" + :"*/3VALUE" from dual'
        self.cursor.prepare(sql)
        self.assertEqual(self.cursor.bindnames(), ["VaLue_2", "*/3VALUE"])

    def test_5209(self):
        "5209 - statement containing simple strings"
        sql = """select '"string_1"', :bind_1, ':string_2' from dual"""
        self.cursor.prepare(sql)
        self.assertEqual(self.cursor.bindnames(), ["BIND_1"])

    def test_5210(self):
        "5210 - bind variables between comment blocks"
        self.cursor.prepare(
            """
            select
                /* comment 1 with /* */
                :a,
                /* comment 2 with another /* */
                :b
                /* comment 3 * * * / */,
                :c
            from dual
            """
        )
        self.assertEqual(self.cursor.bindnames(), ["A", "B", "C"])

    def test_5211(self):
        "5211 - bind variables between q-strings"
        self.cursor.prepare(
            """
            select
                :a,
                q'{This contains ' and " and : just fine}',
                :b,
                q'[This contains ' and " and : just fine]',
                :c,
                q'<This contains ' and " and : just fine>',
                :d,
                q'(This contains ' and " and : just fine)',
                :e,
                q'$This contains ' and " and : just fine$',
                :f
            from dual
            """
        )
        self.assertEqual(
            self.cursor.bindnames(), ["A", "B", "C", "D", "E", "F"]
        )

    @unittest.skipUnless(
        test_env.get_client_version() >= (19, 1), "unsupported client"
    )
    def test_5212(self):
        "5212 - bind variables between JSON constants"
        self.cursor.prepare(
            """
            select
                json_object('foo':dummy),
                :bv1,
                json_object('foo'::bv2),
                :bv3,
                json { 'key1': 57, 'key2' : 58 },
                :bv4
            from dual
            """
        )
        self.assertEqual(self.cursor.bindnames(), ["BV1", "BV2", "BV3", "BV4"])

    def test_5213(self):
        "5213 - multiple line comment with multiple asterisks"
        self.cursor.prepare(
            "/****--select * from :a where :a = 1\n"
            "select * from table_names where :a = 1****/\n"
            "select :table_name, :value from dual"
        )
        self.assertEqual(self.cursor.bindnames(), ["TABLE_NAME", "VALUE"])

    def test_5214(self):
        "5214 - qstring without a closing quote"
        with self.assertRaisesFullCode("DPY-2041"):
            self.cursor.prepare("select q'[something from dual")

    def test_5215_different_space_combinations(self):
        "5215 - different space combinations with :="
        self.cursor.prepare(
            """
            begin :value2 :=
                               :a  + :b  +   :c +:a +3; end;
                               begin :value2
                               :=
                               :a + :c +3; end;
            """
        )
        self.assertEqual(self.cursor.bindnames(), ["VALUE2", "A", "B", "C"])

    def test_5216_binds_between_comment_blocks_with_quotes(self):
        "5216 - bind variables between multiple comment blocks with quotes"
        self.cursor.prepare(
            """
            select
                /* ' comment 1 */
                :a,
                /* "comment " 2 ' */:b
                /* comment 3 '*/,
                :c
                /* comment 4 ""*/
            from dual
            """
        )
        self.assertEqual(self.cursor.bindnames(), ["A", "B", "C"])

    def test_5217_binds_missing_quote_exception(self):
        "5217 - query with a missing end quote"
        with self.assertRaisesFullCode("DPY-2041"):
            self.cursor.prepare("select 'abc, :a from dual")

    def test_5218_binds_missing_quote_exception(self):
        "5218 - q-string with wrong closing symbols"
        with self.assertRaisesFullCode("DPY-2041"):
            self.cursor.prepare("select q'[abc'], 5 from dual")


if __name__ == "__main__":
    test_env.run_test_cases()
