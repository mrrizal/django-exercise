import requests
import argparse

def main(product_name, n):
    url = "http://localhost:8000/v1/products/"
    payload = {
        "name": "Product Name 69",
        "description": "Product Description",
        "variants": [],
        "is_active": True
    }

    for i in range(n):
        variant = {
            "name": f"variant name of {product_name} - {i}",
            "height": 1.3,
            "stock": 10,
            "price": 100000,
            "weight": 1.5,
            "active_time": "2023-08-28T14:46",
            "is_active": False
        }
        payload["variants"].append(variant)

    r = requests.post(url, json=payload)
    if r.status_code not in [200, 201]:
        print(r.json())
    print(r.status_code)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-name", type=str, required=True)
    parser.add_argument("--n-variants", type=int, required=True)

    args = parser.parse_args()
    main(args.product_name, args.n_variants)