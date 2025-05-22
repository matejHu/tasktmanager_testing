import mysql.connector
from dotenv import load_dotenv
import os
from mysql.connector import Error

load_dotenv()

def pripojeni_db():

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            )
        
        if connection.is_connected():
            print("Připojeno k MySQL serveru")
            return connection    
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
def vytvoreni_tabulky(connection):
    """Zkontroluje nebo vytvoří tabulku 'ukoly'."""
    try:
        cursor = connection.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS taskmanager")
        cursor.execute("USE taskmanager")

        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'taskmanager' AND table_name = 'ukoly'
        """)
        (existuje,) = cursor.fetchone()

        if existuje == 0:
            cursor.execute("""
                CREATE TABLE ukoly (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nazev VARCHAR(45) NOT NULL,
                    popis TEXT,
                    stav ENUM('nezahájen', 'probíhá', 'hotovo') DEFAULT 'nezahájen',
                    datum_vytvoreni TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            print("Tabulka 'ukoly' byla vytvořena.")

    except mysql.connector.Error as e:
        print(f"Chyba při vytváření tabulky: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def hlavni_menu():

    connection = None
    
    while True:
        if not connection:
            connection = pripojeni_db()
            if not connection:
                print("Nepodařilo se připojit k databázi.")
        
        if connection:
            vytvoreni_tabulky(connection)
    
        print("\n=== HLAVNÍ NABÍDKA ===")
        print("1. Přidat úkol")
        print("2. Zobrazit úkoly")
        print("3. Aktualizovat úkol")
        print("4. Odstranit úkol")
        print("5. Ukončit program")

        volba = input("Zadejte číslo volby: ")

        if volba == "1":
            pridat_ukol(connection)         
        elif volba == "2":
            zobrazit_ukoly(connection)      
        elif volba == "3":
            aktualizovat_ukol(connection)   
        elif volba == "4":
            odstranit_ukol(connection)      
        elif volba == "5":
            print("Ukončuji program. Nashledanou!")
            break
        else:
            print("Neplatná volba. Zadejte číslo od 1 do 5.")

def pridat_ukol_testDB(connection, nazev, popis):
    # strip odstraní mezery na začátku a konci řetězce
    if not nazev.strip():
        raise ValueError("Chyba, chybí název úkolu") 
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO ukoly (nazev, popis, stav)
        VALUES (%s, %s, %s)
    """, (nazev, popis, "nezahájeno"))
    connection.commit()
    cursor.close()

def pridat_ukol(connection):
    connection.ping(reconnect=True, attempts=3, delay=2)
    print("Přidání nového úkolu")

    try:
        nazev = input("Zadejte název úkolu: ")
        popis = input("Zadejte popis úkolu: ")

        if not nazev:
            print("Název úkolu nesmí být prázdný.")
            return
        if not popis:   
            print("Popis úkolu nesmí být prázdný.")
            return
        
        pridat_ukol_testDB(connection, nazev, popis)
    except Error as e:
        print(f"Chyba při přidávání úkolu: {e}")
        return
    
    print("Úkol byl přidán.")


def zobrazit_ukoly(connection):
    connection.ping(reconnect=True, attempts=3, delay=2)

    print("Zobrazení úkolů se stavem nezahájeno nebo probíhá")

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE stav = 'nezahájeno' OR stav = 'probíhá'")
    ukoly = cursor.fetchall()
    if not ukoly:
        print("Žádné úkoly zatím nebyly přidány.")
    else:
        for ukol in ukoly:
                print(f"ID: {ukol[0]}, Název: {ukol[1]}, Popis: {ukol[2]}, Stav: {ukol[3]}, Datum vytvoření: {ukol[4]}")
        
    cursor.close()

def aktualizovat_ukol_testDB(connection, id_ukolu, stav):
    if id_ukolu < 1:
        raise ValueError("Chyba, vadné id úkolu") 
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE ukoly
        SET stav = %s
        WHERE id = %s
    """, (stav, id_ukolu))
    connection.commit()
    cursor.close()

def aktualizovat_ukol(connection):
    connection.ping(reconnect=True, attempts=3, delay=2)
    print("Aktualizace úkolu")

    zobrazit_ukoly(connection)
    try:
        id_ukolu = input("Zadejte ID úkolu k aktualizaci: ")

        stav = input("Zadejte stav úkolu (probíhá, hotovo): ")
        if stav not in ["probíhá", "hotovo"]:
            print("Neplatný stav. Stav musí být 'probíhá' nebo 'hotovo'.")
            return
        
        id_ukolu = int(id_ukolu)

        aktualizovat_ukol_testDB(connection, id_ukolu, stav)
    except Error as e:
            print(f"Chyba při aktualizování úkolu: {e}")
            return
    print("Úkol byl aktualizován.")

def odstranit_ukol_testDB(connection, id_ukolu):
    if not isinstance(id_ukolu, int) or id_ukolu < 1:
        raise ValueError("Chyba, zadané id musí být kladné celé číslo")

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (id_ukolu,))
    vysledek = cursor.fetchone()
    if not vysledek:
        raise ValueError("Úkol s tímto ID neexistuje.")

    cursor.execute("DELETE FROM ukoly WHERE id = %s", (id_ukolu,))
    connection.commit()
    cursor.close()

def odstranit_ukol(connection):
    connection.ping(reconnect=True, attempts=3, delay=2)
    print("Smazání úkolu")

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM ukoly")
        ukoly = cursor.fetchall()

        if not ukoly:
            print("Žádné úkoly zatím nebyly přidány.")
            return

        for ukol in ukoly:
            print(f"ID: {ukol[0]}, Název: {ukol[1]}, Popis: {ukol[2]}, Stav: {ukol[3]}, Datum vytvoření: {ukol[4]}")

        id_ukolu = input("Zadejte ID úkolu ke smazání: ")

        if not id_ukolu.isdigit():
            print("Zadané ID není platné číslo.")
            return

        id_ukolu = int(id_ukolu)

        cursor.execute("SELECT * FROM ukoly WHERE id = %s", (id_ukolu,))
        vysledek = cursor.fetchone()

        if not vysledek:
            print("Úkol s tímto ID neexistuje.")
        else:
            cursor.execute("DELETE FROM ukoly WHERE id = %s", (id_ukolu,))
            connection.commit()
            print("Úkol byl smazán.")
    finally:
        cursor.close()

if __name__ == "__main__":
    hlavni_menu()