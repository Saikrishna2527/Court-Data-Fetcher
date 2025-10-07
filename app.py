import os
import sqlite3
import random
import json
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "secret!"
DATABASE = "courts_queries.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT,
            case_number TEXT,
            case_year TEXT,
            state TEXT,
            district TEXT,
            raw_html TEXT,
            parsed_json TEXT,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            filename TEXT,
            FOREIGN KEY(query_id) REFERENCES queries(id)
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

def save_query(case_type, case_number, case_year, state, district, raw_html, parsed_json):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO queries (case_type, case_number, case_year, state, district, raw_html, parsed_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (case_type, case_number, case_year, state, district, raw_html, parsed_json),
    )
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

def save_file(query_id, filename):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """INSERT INTO files (query_id, filename) VALUES (?, ?)""", (query_id, filename)
    )
    conn.commit()
    conn.close()

courts = ["High Court", "District Court"]
states = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Lakshadweep", "Delhi", "Puducherry"
]
districts = {
    # "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur"],
    # "Delhi": ["New Delhi", "South Delhi", "East Delhi", "North Delhi"],
    # "Karnataka": ["Bangalore", "Mysore", "Mangalore"],
    # "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    # "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    # "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra"],
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore",
                       "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"],
    "Arunachal Pradesh": ["Tawang", "West Kameng", "East Kameng", "Papum Pare", "Kurung Kumey", "Kra Daadi", "Lower Subansiri",
                          "Upper Subansiri", "West Siang", "East Siang", "Lower Siang", "Upper Siang", "Lower Dibang Valley",
                          "Dibang Valley", "Anjaw", "Lohit", "Namsai", "Changlang", "Tirap"],
    "Assam": ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang",
              "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Jorhat",
              "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli",
              "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "Tinsukia", "Udalguri"],
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar",
              "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar",
              "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur",
              "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura",
              "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur",
                     "Dantewada", "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa", "Jashpur", "Kabirdham",
                     "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
                     "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad",
                "Chhota Udepur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath",
                "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada",
                "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat",
                "Surendranagar", "Tapi", "Vadodara", "Valsad"],
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar",
                "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula",
                "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Lahaul and Spiti", "Mandi",
                        "Shimla", "Sirmaur", "Solan", "Una"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih",
                 "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga",
                 "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj", "Sarwak", "West Singhbhum"],
    "Karnataka": ["Bagalkot", "Bangalore Rural", "Bangalore Urban", "Belagavi", "Bellary", "Bidar", "Chamarajanagar",
                  "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad",
                  "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru",
                  "Raichur", "Ramanagara", "Shimoga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode",
               "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
    "Madhya Pradesh": ["Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
                       "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
                       "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
                       "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
                       "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
                       "Shahdol", "Shajapur", "Sheopur", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain",
                       "Umaria", "Vidisha"],
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur",
                    "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City",
                    "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani",
                    "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane",
                    "Wardha", "Washim", "Yavatmal"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching",
                "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal",
                "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills",
                  "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "West Garo Hills", "West Jaintia Hills",
                  "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Serchhip"],
    "Nagaland": ["Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Tuensang",
                 "Wokha", "Zunheboto"],
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh",
               "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi",
               "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
               "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur",
               "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga",
               "Muktsar", "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar", "Sangrur", "Tarn Taran"],
    "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner",
                  "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh",
                  "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli",
                  "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar",
                  "Sirohi", "Tonk", "Udaipur"],
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
                   "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
                   "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
                   "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
                   "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
                   "Tiruchirappalli", "Tirunelveli", "Tirupur", "Tiruvallur", "Tiruvannamalai",
                   "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally",
                  "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad",
                  "Mahabubnagar", "Mancherial", "Medak", "Medchal", "Mulugu", "Nagarkurnool", "Nalgonda",
                  "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet",
                  "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh",
                      "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti",
                      "Bhadohi", "Bijnor", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah",
                      "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur",
                      "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur",
                      "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar",
                      "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura",
                      "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh",
                      "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur",
                      "Shamli", "Shravasti", "Siddharth Nagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao",
                      "Varanasi"],
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital",
                    "Pauri Garhwal", "Pilibhit", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly",
                    "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia",
                    "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur",
                    "Purulia", "South 24 Parganas", "Uttar Dinajpur"]
}


case_types = [
    "Civil Appeal", "Criminal Appeal", "Writ Petition", "Civil Original",
    "Criminal Original", "Family Case", "Land Case", "Revenue Case", "Company Case", "Miscellaneous"
]
case_numbers = ["101", "102", "150", "200", "300", "400", "500", "601", "700", "800"]
case_years = ["2025", "2024", "2023", "2022", "2021"]

petitioners_list = [
    ["Ramesh Kumar", "Suresh Patil"], ["Anita Sharma", "Vikram Singh"],
    ["Pooja Verma", "Rohit Gupta"], ["Sunita Joshi", "Ajay Mehta"],
    ["Neha Jain", "Manish Pillai"], ["Priya Nair", "Sachin Rao"],
    ["Deepak Singh", "Arvind Kumar"], ["Kavita Das", "Mukesh Sharma"],
    ["Alok Verma", "Suraj Yadav"], ["Sanjay Kumar", "Aditya Sinha"],
]

respondents_list = [
    ["Sapna", "Anil Singh"], ["Suman Rao", "Rajesh Kumar"],
    ["Geeta Patel", "Dinesh Khanna"], ["Jyoti Mishra", "Pradeep Tiwari"],
    ["Lata Das", "Niraj Shah"], ["Seema Gupta", "Rakesh Chaturvedi"],
    ["Tarun Singh", "Mahesh Sharma"], ["Smita Ghosh", "Vijay Kumar"],
    ["Neeraj Pandey", "Arjun Reddy"], ["Vikash Chawla", "Karan Mehra"],
]

relevant_acts = {
    "Civil Appeal": [("Civil Procedure Code", "85"), ("Civil Procedure Code", "86")],
    "Criminal Appeal": [("Criminal Procedure Code", "107"), ("Criminal Procedure Code", "108")],
    "Writ Petition": [("Constitution of India", "32"), ("Constitution of India", "226")],
    "Civil Original": [("Civil Procedure Code", "89"), ("Specific Relief Act", "12")],
    "Criminal Original": [("Indian Penal Code", "302"), ("Indian Penal Code", "376")],
    "Family Case": [("Hindu Marriage Act", "13"), ("Hindu Marriage Act", "14")],
    "Land Case": [("Land Acquisition Act", "23"), ("Land Acquisition Act", "24")],
    "Revenue Case": [("Revenue Recovery Act", "5"), ("Revenue Recovery Act", "10")],
    "Company Case": [("Companies Act", "100"), ("Companies Act", "101")],
    "Miscellaneous": [("IPC", "420"), ("Criminal Procedure Code", "41")],
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        case_type = request.form.get("case_type")
        case_number = request.form.get("case_number")
        case_year = request.form.get("case_year")
        state = request.form.get("state")
        district = request.form.get("district")
        court_type = request.form.get("court_type")

        if case_number in case_numbers:
            idx = case_numbers.index(case_number)
        else:
            idx = random.randint(0, len(petitioners_list) - 1)

        petitioners = petitioners_list[idx]
        respondents = respondents_list[idx]

        acts_to_show = [{"act_name": act, "section": sec} for (act, sec) in relevant_acts.get(case_type, [])]

        details = {
            "court_type": court_type,
            "case_type": case_type,
            "filing_number": f"{case_number}/{case_year}",
            "filing_date": "07-07-2025",
            "registration_number": "133/2025",
            "registration_date": "07-07-2025",
            "cnr_number": "hpch01001804/2025",
            "first_hearing": "18 July 2025",
            "decision_date": "18 September 2025",
            "case_status": "Pending",
            "nature_of_disposal": "Service",
            "judge": "I District and sessions judge",
            "petitioners": petitioners,
            "respondents": respondents,
            "orders": [{"number": "1", "date": "22 July 2025", "details": "zima orders or judicial", "pdf_link": "sample_order.pdf"}],
            "histories": [{"entry": 1, "judge": "District and sessions judge", "business_date": "18 July 2025",
                "hearing_date": "22 July 2025", "purpose": "office report"}],
            "acts": acts_to_show,
            "processes": [{"id": "001", "process_date": "18-07-2025", "title": "Summons for disposal of suit",
                          "party_name": respondents[0], "issued_status": "Issued"}],
        }
        raw_html = "[Hardcoded Data]"
        parsed_json = json.dumps(details)
        query_id = save_query(case_type, case_number, case_year, state, district, raw_html, parsed_json)
        return redirect(url_for('show_details', query_id=query_id))

    return render_template("index.html", courts=courts, states=states, districts=districts,
                           case_types=case_types, case_numbers=case_numbers, case_years=case_years,
                           details=None, selected_state=None, selected_district=None)


@app.route("/details/<int:query_id>")
def show_details(query_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT parsed_json FROM queries WHERE id = ?", (query_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        flash("No case details found for the query ID.", "danger")
        return redirect(url_for("index"))
    details = json.loads(row[0])
    flash("Case details fetched successfully ✓", "success")
    return render_template("details.html", details=details)


@app.route("/download/<filename>")
def download_file(filename):
    try:
        return send_from_directory(os.path.join(app.root_path, "static"), filename, as_attachment=True)
    except Exception as e:
        flash("Download error: " + str(e))
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
