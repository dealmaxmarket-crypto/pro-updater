import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd

# Список твоїх 9 посилань на прайси постачальників
FEED_URLS = [
    "https://opt-drop.com/storage/xml/opt-drop-29.xml",
    "https://aveon.net.ua/yandex_market.xml?hash_tag=7b71fadcc4a12f03cf26a304da032fba",
    "https://feed.lugi.com.ua/index.php?route=extension/feed/unixml/prommulti",
    "https://6kilometr.com.ua/yandex_market.xml?hash_tag=a05443bbe29b8152f7f23e09cd8c0fac",
    "https://livelyshop.com.ua/products_feed.xml?hash_tag=e0e046a4f54904aacd559e46afd96a8e",
    "https://velocompany.com.ua/products_feed.xml?hash_tag=dd9d6354c41b68d6d3d059d15f2dac4d",
    "https://modern.best-time.biz/uk/feed/rozetka?priceua_price=1",
    "https://i-maxi.com.ua/yandex_market.xml?hash_tag=3862084c32af01bfd3be5efc7110b84c",
    "https://geo-market.salesdrive.me/export/yml/export.yml?publicKey=g7HidIKJWTjhyiMvbsUQKuztsuqHTR2-gLac21sdTbwAVGX81FQSJ0FnelqaQAni"
]

def load_supplier_active_skus(urls):
    """Завантажує всі прайси та збирає артикули товарів, які є в наявності"""
    active_skus = set()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in urls:
        try:
            print(f"Завантажую прайс: {url[:40]}...")
            req = urllib.request.Request(url, headers=headers)
            # Зменшено таймаут до 10 секунд, щоб скрипт не зависав через мертві сервери
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                
            root = ET.fromstring(xml_data)
            for offer in root.iter('offer'):
                available = offer.get('available')
                if available == 'true' or available is None:
                    vendor_code_elem = offer.find('vendorCode')
                    if vendor_code_elem is not None and vendor_code_elem.text:
                        active_skus.add(str(vendor_code_elem.text).strip())
                    else:
                        code_elem = offer.find('code')
                        if code_elem is not None and code_elem.text:
                            active_skus.add(str(code_elem.text).strip())
        except Exception as e:
            print(f"ПРОПУЩЕНО через помилку/таймаут {url[:40]}: {e}")
            
    print(f"Успішно зібрано активних артикулів від постачальників: {len(active_skus)}")
    return active_skus

def generate_prom_import_file(excel_path, active_skus, output_xml_path):
    """Порівнює базу Prom з прайсами і створює XML для швидкого імпорту наявності"""
    df = pd.read_excel(excel_path, sheet_name='Export Products Sheet')
    
    root = ET.Element('yml_catalog')
    shop = ET.SubElement(root, 'shop')
    offers = ET.SubElement(shop, 'offers')
    
    updated_count = 0
    for _, row in df.iterrows():
        sku = str(row.get('Код_товару', '')).strip()
        unique_id = row.get('Унікальний_ідентифікатор')
        
        if not unique_id or pd.isna(unique_id):
            continue
            
        is_available = 'true' if sku in active_skus else 'false'
        
        offer = ET.SubElement(offers, 'offer', id=str(unique_id))
        stock_elem = ET.SubElement(offer, 'stock_quantity')
        stock_elem.text = '10' if is_available == 'true' else '0'
        offer.set('available', is_available)
        updated_count += 1

    tree = ET.ElementTree(root)
    tree.write(output_xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Готово! Згенеровано файл для {updated_count} товарів: {output_xml_path}")

if __name__ == "__main__":
    active_skus = load_supplier_active_skus(FEED_URLS)
    generate_prom_import_file('export-products-27-10-26_16-13-37---.xlsx', active_skus, 'prom_update_feed.xml')
