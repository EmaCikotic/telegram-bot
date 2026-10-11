import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlencode, urlsplit, urlunsplit

url = "https://www.studentski-servis.com/studenti/prosta-dela?isci=1&dm1s=1&skD[]=004&skD[]=A832&skD[]=A210&skD[]=A055&skD[]=A078&skD[]=A090&skD[]=A095&hourlyratefrom=7.73&hourlyrateto=31&hourly_rate=7.73%3B31"

# test_url_for_pagination = "https://www.studentski-servis.com/studenti/prosta-dela?isci=1&dm1s=1&hourlyratefrom=7.73&hourlyrateto=31&hourly_rate=7.73%3B31&regija[]=osrednjeslovenska"


def fetch_student_jobs():

    url_parts = urlsplit(url)
    params = parse_qs(url_parts.query, keep_blank_values=True)
    print(params)

    results = []
    seen = set()
    page = 1

    while True:
        params["page"] = [str(page)]
        query = urlencode(params, doseq=True)
        print(query)

        page_url = urlunsplit(
            (
                url_parts.scheme,
                url_parts.netloc,
                url_parts.path,
                query,
                url_parts.fragment,
            )
        )

        response = requests.get(page_url, timeout=30)

        print("status:", response.status_code)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        titles = soup.select("h5.mb-0")  # to find titles

        print("Titles found: ", len(titles))

        count_before = len(results)

        for title in titles:
            job = title.parent

            share = job.select_one("[data-share]")

            if share is None:
                print("No link to share")
                continue

            link = urljoin(url, share["data-share"])

            if link in seen:
                continue

            seen.add(link)

            headings = job.select("h5.mb-0")
            names = []

            for heading in headings:
                names.append(heading.get_text(strip=True))

            name = " - ".join(names)  # PROGRAMIRANJE — BACK-END PROGRAMER

            details = job.select("p.mb-0.text-break")
            payment = job.select_one(".job-payment")

            company = details[0].get_text(strip=True) if details else ""
            company = company or "Company not listed"
            location = (
                details[1].get_text(strip=True) if len(details) > 1 else "Not available"
            )
            pay = payment.get_text(" ", strip=True) if payment else "Not available"

            advert = {
                "title": name,
                "company": company,
                "location": location,
                "pay": pay,
                "link": link,
            }

            results.append(advert)

        if len(results) == count_before:
            break

        page += 1  # go to the next page
    return results


if __name__ == "__main__":
    ads = fetch_student_jobs()
    print("Saved ads: ", len(ads))
