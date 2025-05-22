from taskmanager import pridat_ukol_testDB, aktualizovat_ukol_testDB, odstranit_ukol_testDB
import mysql.connector
import pytest

TEST_DB_NAME = "taskmanager_test"

@pytest.fixture(scope="module")
def db_connection():
    # Setup: vytvoření databáze a tabulky
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="password"
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME}")
    cursor.execute(f"USE {TEST_DB_NAME}")
    cursor.execute("DROP TABLE IF EXISTS ukoly")
    cursor.execute("""
        CREATE TABLE ukoly (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(45) NOT NULL,
            popis TEXT,
            stav ENUM('nezahájen', 'probíhá', 'hotovo') DEFAULT 'nezahájen',
            datum_vytvoreni TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

    # Připojení pro testy
    connection = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="password",
        database=TEST_DB_NAME
    )
    yield connection
    connection.close()


#negativní test - přidání úkolu s prázdným názvem
def test_pridat_ukol_negativ(db_connection):
    with pytest.raises(ValueError, match="Chyba, chybí název úkolu"):
        pridat_ukol_testDB(db_connection, "", "Popis úkolu")

#positivní test - přidání úkolu s vyplněnými parametry
def test_pridat_ukol_positiv(db_connection):
    pridat_ukol_testDB(db_connection, "Úkol 1", "Popis úkolu")

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE nazev = %s", ("Úkol 1",))
    result = cursor.fetchone()
    print(result)
    
    assert result is not None, "Úkol nebyl nalezen v databázi"
    assert result[1] == "Úkol 1"
    assert result[2] == "Popis úkolu"

    cursor.close()

#negativní test - aktualizace úkolu s prázdným názvem
def test_aktualizovat_ukol_negativ(db_connection):
    with pytest.raises(ValueError, match="Chyba, vadné id úkolu"):
        aktualizovat_ukol_testDB(db_connection, -1, "")

#positivní test - aktualizace úkolu s vyplněnými parametry
def test_aktualizovat_ukol_positiv(db_connection):
    cursor = db_connection.cursor()

    cursor.execute("""
        INSERT INTO ukoly (nazev, popis, stav)
        VALUES (%s, %s, %s)
    """, ("Úkol k aktualizaci", "Popis", "nezahájen"))
    db_connection.commit()


    cursor.execute("SELECT id FROM ukoly WHERE nazev = %s", ("Úkol k aktualizaci",))
    id_ukolu = cursor.fetchone()[0]

    aktualizovat_ukol_testDB(db_connection, id_ukolu, "hotovo")

    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (id_ukolu,))
    stav = cursor.fetchone()[0]
    print(stav)
    cursor.close()

    assert stav == "hotovo"

#positivni test = odstranění úkolu
def test_odstranit_ukol_positiv(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO ukoly (nazev, popis) VALUES (%s, %s)", ("Test smazání", "Popis"))
    db_connection.commit()
    cursor.execute("SELECT id FROM ukoly WHERE nazev = %s", ("Test smazání",))
    id_ukolu = cursor.fetchone()[0]
    cursor.close()

    print(id_ukolu)

    odstranit_ukol_testDB(db_connection, id_ukolu)

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (id_ukolu,))
    assert cursor.fetchone() is None
    cursor.close()

#negativní test - odstranění úkolu s neexistujícím id
def test_odstranit_ukol_negativ(db_connection):
    with pytest.raises(ValueError, match="Chyba, zadané id musí být kladné celé číslo"):
        odstranit_ukol_testDB(db_connection, "neplatne_id")