import sure  # noqa
import pytest

from py_partiql_parser import Parser
from py_partiql_parser._internal.parser import FromParser

MISSING = "TODO"

# All examples taken from the official specification:
# https://partiql.org/assets/PartiQL-Specification.pdf
#


class Test_Chapter4:
    """
    Path Navigation
    """

    def test_example2a(self):
        query = "SELECT VALUE v FROM [1, 2, 3] AS v"
        expected_result = [1, 2, 3]
        assert_result(query, expected_result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example2b(self):
        query = "SELECT VALUE v FROM UNPIVOT {'a':1, 'b':2} AS v"
        expected_result = [1, 2]
        assert_result(query, expected_result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example2c(self):
        query = "SELECT t.* FROM <<{'a':1, 'b':1}, {'a':2, 'b':2}>> AS t"
        expected_result = [{"a": 1, "b": 1}, {"a": 2, "b": 2}]
        assert_result(query, expected_result)


class Test_Chapter5:
    """
    FROM Clause Semantics
    """

    someOrderedTable: [{"a": 0, "b": 0}, {"a": 1, "b": 1}]
    justATuple: {"amzn": 840.05, "tdc": 31.06}

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example4(self):
        from_clause = "FROM someOrderedTable AS x AT y"
        expected_output = [
            {"x": {"a": 0, "b": 0}, "y": 0},
            {"x": {"a": 1, "b": 1}, "y": 1},
        ]
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example5(self):
        from_clause = "FROM someOrderedTable AS x"
        expected_output = [{"x": {"a": 0, "b": 0}}, {"x": {"a": 1, "b": 1}}]
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example6(self):
        from_clause = "FROM someOrderedTable[0].a AS x"
        expected_output = [{"x": 0}]
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example7(self):
        from_clause = "FROM someOrderedTable[0].c AS x"
        expected_output = {"x": MISSING}
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example8(self):
        from_clause = "FROM UNPIVOT justATuple AS price AT symbol"
        expected_output = [
            {"price": 840.05, "symbol": "amzn"},
            {"price": 31.06, "symbol": "tdc"},
        ]
        assert_from_result(from_clause, expected_output)

    input = {
        "customers": [{"id": 5, "name": "Joe"}, {"id": 7, "name": "Mary"}],
        "orders": [{"custId": 7, "productId": 101}, {"custId": 7, "productId": 523}],
    }

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example9(self):
        from_clause = "FROM customers AS c, orders AS o"
        expected_output = [
            {"c": {"id": 5, "name": "Joe"}, "o": {"custId": 7, "productId": 101}},
            {"c": {"id": 5, "name": "Joe"}, "o": {"custId": 7, "productId": 523}},
            {"c": {"id": 7, "name": "Mary"}, "o": {"custId": 7, "productId": 101}},
            {"c": {"id": 7, "name": "Mary"}, "o": {"custId": 7, "productId": 523}},
        ]
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example10(self):
        input = {
            "sensors": [
                {"readings": [{"v": 1.3}, {"v": 2}]},
                {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]},
            ]
        }
        from_clause = "FROM sensors AS s, s.readings AS r"
        expected_output = [
            {"s": {"readings": [{"v": 1.3}, {"v": 2}]}, "r": {"v": 1.3}},
            {"s": {"readings": [{"v": 1.3}, {"v": 2}]}, "r": {"v": 2}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.7}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.8}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.9}},
        ]
        assert_from_result(from_clause, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example11(self):
        input = {
            "sensors": [
                {"readings": [{"v": 1.3}, {"v": 2}]},
                {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]},
                {"readings": []},
            ]
        }
        from_clause = "FROM sensors AS s LEFT CROSS JOIN s.readings AS r"
        expected_output = [
            {"s": {"readings": [{"v": 1.3}, {"v": 2}]}, "r": {"v": 1.3}},
            {"s": {"readings": [{"v": 1.3}, {"v": 2}]}, "r": {"v": 2}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.7}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.8}},
            {"s": {"readings": [{"v": 0.7}, {"v": 0.8}, {"v": 0.9}]}, "r": {"v": 0.9}},
            {"s": {"readings": []}, "r": None},
        ]
        assert_from_result(from_clause, expected_output)


class Test_Chapter6:
    """
    SELECT clauses
    """

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example12(self):
        query = """SELECT VALUE 2*x.a
    FROM [{'a':1}, {'a':2}, {'a':3}] as x"""
        result = [2, 4, 6]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example13(self):
        query = """SELECT VALUE {'a':v.a, 'b':v.b}
    FROM [{'a':1, 'b':1}, {'a':2, 'b':2}] AS v"""
        result = [{"a": 1, "b": 1}, {"a": 2, "b": 2}]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example14(self):
        # This should only pass in PERMISSIVE mode
        # This should fail in Type-Checking mode
        query = """SELECT VALUE {v.a: v.b}
    FROM [{'a':'legit', 'b':1}, {'a':400, 'b':2}] AS v"""
        result = [{"legit": 1}, {}]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example15(self):
        """
        Treatment of duplicate attribute names It is possible that the constructed tuples contain twice or more the same attribute name.
        :return:
        """
        query = """SELECT VALUE {v.a: v.b, v.c: v.d}
    FROM [{'a':'same', 'b':1, 'c':'same', 'd':2}] AS v"""
        result = [{"same": 1, "same": 2}]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example16(self):
        """
        Array Constructors
        :return:
        """
        query = """SELECT VALUE [v.a, v.b]
    FROM [{'a':1, 'b':1}, {'a':2, 'b':2}] AS V"""
        result = [[1, 1], [2, 2]]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example17(self):
        """
        Bag Constructors
        :return:
        """
        query = """SELECT VALUE <<v.a, v.b>>
    FROM [{'a':1, 'b':1}, {'a':2, 'b':2}] AS v"""
        result = [{1, 1}, {2, 2}]
        assert_result(query, result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example18(self):
        """
        when constructing tuples
        Whenever during tuple construction an attribute value evaluates to MISSING,
        then the particular attribute/value is omitted from the constructed tuple
        :return:
        """
        query = """SELECT VALUE {'a':v.a, 'b':v.b}
FROM [{'a':1, 'b':1}, {'a':2}]"""
        expected_output = [{"a": 1, "b": 1}, {"a": 2}]
        assert_result(query, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example19(self):
        """
        when constructing arrays
        Whenever an array element evaluates to MISSING, the resulting array will contain a MISSING.
        :return:
        """
        query = """SELECT VALUE [v.a, v.b]
FROM [{'a':1, 'b':1}, {'a':2}]"""
        expected_output = [[1, 1], [2, MISSING]]
        assert_result(query, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example20(self):
        """
        when constructing bags
        Whenever an element of a bag evaluates to MISSING, the resulting bag will contain a corresponding MISSING.
        :return:
        """
        query = """SELECT VALUE v.b
FROM [{'a':1, 'b':1}, {'a':2}]"""
        expected_output = [1, MISSING]
        assert_result(query, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example21(self):
        """
        when constructing bags
        Whenever an element of a bag evaluates to MISSING, the resulting bag will contain a corresponding MISSING.
        :return:
        """
        query = """SELECT VALUE <<v.a, v.b>>
FROM [{'a':1, 'b':1}, {'a':2}]"""
        expected_output = [{1, 1}, {2, MISSING}]
        assert_result(query, expected_output)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example24(self):
        query = """SELECT x.*
    FROM [{'a':1, 'b':1}, {'a':2}, 'foo'] AS x"""
        expected_output = [{"a": 1, "b": 1}, {"a": 2}, {"_1": "foo"}]
        assert_result(query, expected_output)

    database = {
        "sensors": [{"sensor": 1}, {"sensor": 2}],
        "logs": [
            {"sensor": 1, "co": 0.4},
            {"sensor": 1, "co": 0.2},
            {"sensor": 2, "co ": 0.3},
        ],
    }

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example25(self):
        query = """SELECT VALUE {’sensor’: s.sensor,
’readings’: (SELECT VALUE l.co
FROM logs AS l
WHERE l.sensor = s.sensor
)
}
FROM sensors AS s"""
        expected_result = [
            {"sensor": 1, "readings": {0.4, 0.2}},
            {"sensor": 2, "readings": {0.3}},
        ]
        assert_result(query, expected_result)

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example26(self):
        database = {
            "sensors": [
                {"no2": 0.6, "co": 0.7, "co2": 0.5},
                {"no2": 0.5, "co": 0.4, "co2": 1.3},
            ]
        }
        query = """SELECT VALUE (PIVOT v AT g
FROM UNPIVOT r AS v AT g
WHERE g LIKE ’co%’)
FROM sensors AS r"""
        expected_result = [{"co": 0.7, "co2": 0.5}, {"co": 0.4, "co2": 1.3}]
        assert_result(query, expected_result)


class Test_Chapter7:
    """
    Functions
    """

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example27(self):
        query = """SELECT VALUE {’a’:3*v.a, ’b’:3*(CAST v.b AS INTEGER)}
FROM [{’a’:1, ’b’:’1’}, {’a’:2}] v"""
        expected_result = [{"a": 3, "b": 3}, {"a": 6}]
        assert_result(query, expected_result)


class Test_Chapter8:
    """
    WHERE clause
    """

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_example30(self):
        query = """SELECT VALUES v.a
FROM [{’a’:1, ’b’:true}, {’a’:2, ’b’:null}, {’a’:3}] v
WHERE v.b"""
        expected_result = {1}
        assert_result(query, expected_result)


class Test_Chapter9:
    """
    Coercion of subqueries
    """

    pass


class Test_Chapter10:
    """
    Scoping rules
    """

    pass


class Test_Chapter11:
    """
    GROUP BY clause
    """

    pass


class Test_Chapter12:
    """
    ORDER BY clause
    """

    pass


def assert_result(query, result):
    Parser().parse(query).should.equal(result)


def assert_from_result(from_clause, expected_output):
    FromParser().parse(from_clause).should.equal(expected_output)
