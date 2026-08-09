import httpx2 as httpx


def main() -> None:
    ip = "8.8.8.8"
    url = f"http://ip-api.com/json/{ip}"
    with httpx.Client(timeout=2.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

    print(
        {
            "country": data.get("country"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
        }
    )


if __name__ == "__main__":
    main()


"""
{
    "query": "3.253.92.109",
    "status": "success",
    "continent": "Europe",
    "continentCode": "EU",
    "country": "Ireland",
    "countryCode": "IE",
    "region": "L",
    "regionName": "Leinster",
    "city": "Dublin",
    "district": "",
    "zip": "D02",
    "lat": 53.3498,
    "lon": -6.26031,
    "timezone": "Europe/Dublin",
    "offset": 0,
    "currency": "EUR",
    "isp": "Amazon Technologies Inc.",
    "org": "AWS EC2 (eu-west-1)",
    "as": "AS16509 Amazon.com, Inc.",
    "asname": "AMAZON-02",
    "mobile": false,
    "proxy": false,
    "hosting": true
}


http://ip-api.com/json/24.48.0.1

Frequently Asked Questions
How often do you update your database?
We update our database as soon as we have new information about an IP block. For each API request, you will always have the most accurate location data, without having to worry about updating a local database.

Are you still going to be here next year? Can I use your API in production?
IP-API has been running since 2012 and we are now providing one of the most popular and reliable IP Geolocation API.

Do I need an API key for the free endpoint?
We will never require an API key or registration and the API schema will not change.

How many requests can I do?
Our endpoints are limited to 45 HTTP requests per minute from an IP address. If you go over this limit your requests will be throttled (HTTP 429) until your rate limit window is reset.
If you need unlimited queries, please see our pro service.

What is the average response time of the API?
With dedicated servers in US, EU and APAC, a network based on Anycast technology, and highly optimized software we achieve real response times of under 50 milliseconds in most parts of the world.

Can I use your API on my commercial website?
We do not allow commercial use of the free endpoint. Please see our pro service for SSL access, unlimited queries, usage statistics and commercial support.
"""
