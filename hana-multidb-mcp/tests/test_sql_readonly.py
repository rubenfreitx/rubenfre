import pytest
from src.guards.sql_readonly import assert_readonly


# ── Allowed statements ────────────────────────────────────────────────────────

def test_select_simple():
    assert_readonly("SELECT 1 FROM DUMMY")


def test_select_multiline():
    assert_readonly(
        "SELECT col1, col2\n"
        "FROM my_schema.my_table\n"
        "WHERE col1 = 'abc'"
    )


def test_with_cte():
    assert_readonly(
        "WITH cte AS (SELECT id FROM t) SELECT * FROM cte"
    )


def test_explain():
    assert_readonly("EXPLAIN SELECT * FROM my_table")


def test_show():
    assert_readonly("SHOW TABLES")


def test_trailing_semicolon_allowed():
    assert_readonly("SELECT 1 FROM DUMMY;")


def test_case_insensitive_select():
    assert_readonly("select 1 from dummy")


def test_case_insensitive_with():
    assert_readonly("with cte as (select 1) select * from cte")


def test_leading_comment_select():
    assert_readonly("-- fetch count\nSELECT COUNT(*) FROM t")


def test_block_comment_before_select():
    assert_readonly("/* ok */ SELECT 1 FROM DUMMY")


# ── Blocked DML ───────────────────────────────────────────────────────────────

def test_update_blocked():
    with pytest.raises(ValueError, match="UPDATE"):
        assert_readonly("UPDATE t SET col = 1 WHERE id = 1")


def test_delete_blocked():
    with pytest.raises(ValueError, match="DELETE"):
        assert_readonly("DELETE FROM t WHERE id = 1")


def test_insert_blocked():
    with pytest.raises(ValueError, match="INSERT"):
        assert_readonly("INSERT INTO t VALUES (1)")


def test_merge_blocked():
    with pytest.raises(ValueError, match="MERGE"):
        assert_readonly("MERGE INTO t USING src ON t.id = src.id WHEN MATCHED THEN UPDATE SET t.v = src.v")


def test_upsert_blocked():
    with pytest.raises(ValueError, match="UPSERT"):
        assert_readonly("UPSERT t VALUES (1, 2)")


# ── Blocked DDL ───────────────────────────────────────────────────────────────

def test_create_blocked():
    with pytest.raises(ValueError, match="CREATE"):
        assert_readonly("CREATE TABLE t (id INT)")


def test_drop_blocked():
    with pytest.raises(ValueError, match="DROP"):
        assert_readonly("DROP TABLE t")


def test_alter_blocked():
    with pytest.raises(ValueError, match="ALTER"):
        assert_readonly("ALTER TABLE t ADD COLUMN c VARCHAR(10)")


def test_truncate_blocked():
    with pytest.raises(ValueError, match="TRUNCATE"):
        assert_readonly("TRUNCATE TABLE t")


# ── Blocked procedures / transactions ─────────────────────────────────────────

def test_call_blocked():
    with pytest.raises(ValueError, match="CALL"):
        assert_readonly("CALL my_proc()")


def test_execute_blocked():
    with pytest.raises(ValueError, match="EXECUTE"):
        assert_readonly("EXECUTE my_proc()")


def test_commit_blocked():
    with pytest.raises(ValueError, match="COMMIT"):
        assert_readonly("COMMIT")


def test_rollback_blocked():
    with pytest.raises(ValueError, match="ROLLBACK"):
        assert_readonly("ROLLBACK")


def test_set_blocked():
    with pytest.raises(ValueError, match="SET"):
        assert_readonly("SET SCHEMA my_schema")


# ── Multi-statement protection ────────────────────────────────────────────────

def test_multi_statement_blocked():
    with pytest.raises(ValueError, match="Multiple"):
        assert_readonly("SELECT 1; SELECT 2")


def test_multi_statement_with_dml_blocked():
    with pytest.raises(ValueError, match="Multiple"):
        assert_readonly("SELECT 1; DELETE FROM t")


# ── Comment injection attempts ────────────────────────────────────────────────

def test_comment_bypass_line_comment():
    with pytest.raises(ValueError):
        assert_readonly("-- safe\nDELETE FROM t")


def test_comment_bypass_block_comment():
    with pytest.raises(ValueError):
        assert_readonly("/* ok */ DELETE FROM t")


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_raises():
    with pytest.raises(ValueError, match="Empty"):
        assert_readonly("")


def test_only_comment_raises():
    with pytest.raises(ValueError, match="Empty"):
        assert_readonly("-- just a comment")


def test_unknown_statement_blocked():
    with pytest.raises(ValueError, match="Unrecognised"):
        assert_readonly("EXEC_PROC something()")
