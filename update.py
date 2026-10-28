import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io

# 1. Посилання на постачальників
SUPPLIER_URLS = [
    # Встав сюди свої посилання на XML/YML прайси постачальників, наприклад:
    # "https://example.com/supplier1.xml",
]

def main():
    supplier_stock = {}

    # Завантажуємо прайси постачальників
    for url in SUPPLIER_URLS:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for offer in root.iter('offer'):
                    offer_id = offer.attrib.get('id')
                    available = offer.attrib.get('available', 'false')
                    stock_qty = offer.findtext('stock_quantity', '0')
                    
                    if offer_id:
                        supplier_stock[str(offer_id)] = {
                            'available': available,
                            'quantity': stock_qty
                        }
        except Exception as e:
            print(f"Помилка завантаження прайсу {url}: {e}")

    # Створюємо XML тільки для товарів, які є у постачальника
    root = ET.Element("yml_catalog")
    shop = ET.SubElement(root, "shop")
    offers = ET.SubElement(shop, "offers")

    for item_id, data in supplier_stock.items():
        offer_el = ET.SubElement(offers, "offer", id=item_id, available=data['available'])
        stock_el = ET.SubElement(offer_el, "stock_quantity")
        stock_el.text = str(data['quantity'])

    # Записуємо у файл
    tree = ET.ElementTree(root)
    tree.write("prom_update_feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"Готово! Додано товарів у фід: {len(supplier_stock)}")

if __name__ == "__main__":
    main()
