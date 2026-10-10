import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://www.studentski-servis.com/studenti/prosta-dela?kljb=&page=1&isci=1&sort=&dm1s=1&regija%5B%5D=osrednjeslovenska&regija%5B%5D=ljubljana-z-okolico&regija%5B%5D=domzale-kamnik&regija%5B%5D=grosuplje-z-okolico&regija%5B%5D=vrhnika-z-okolico&skD%5B%5D=004&skD%5B%5D=A832&skD%5B%5D=A210&skD%5B%5D=A055&skD%5B%5D=A078&skD%5B%5D=A090&skD%5B%5D=A095&hourlyratefrom=7.73&hourlyrateto=31&hourly_rate=7.73%3B31"


def fetch_student_jobs():

    response = requests.get(url, timeout=30)

    print("status:", response.status_code)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    titles = soup.select("h5.mb-0")  # to find titles

    print("Titles found: ", len(titles))


    results = []

    for title in titles:
        job = title.parent

        share = job.select_one("[data-share]")

        if share is None:
            print("No link to share")
            continue

        link = urljoin(url, share["data-share"])

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
    return results


if __name__ == "__main__":
    ads = fetch_student_jobs()
    print("Saved ads: ", len(ads))
