from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
import logging
import mysql.connector as conn
from flask_cors import cross_origin
import os

mylist = []
mydb = conn.MySQLConnection()

app = Flask(__name__)

logging.basicConfig(filename="scrapper.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# helper function
def get_course_name():
    search = request.form['course']
    return search


# database insertion
def insertdb():
    global mydb, mylist
    try:
        if not mydb.is_connected():
            logging.info("inside if block")
            mydb = conn.connect(host='localhost', user='root', passwd='sqldaru4')
            cursor = mydb.cursor()
            logging.info("created cursor")
            cursor.execute('create database IF NOT EXISTS ineuronai')
            logging.info('created database ')
            cursor.execute("create table IF NOT EXISTS ineuronai.course(Course_name VARCHAR(100),Course_Intro VARCHAR(900), Course_syllabus VARCHAR(2000), Course_features VARCHAR(3000), Course_requirements VARCHAR(1000), Course_mentors VARCHAR(200), Course_price VARCHAR(100))")
            for mydic in mylist:
                cursor.execute('insert ignore into ineuronai.course values("{0}", "{1}","{2}","{3}","{4}","{5}", "{6}")'.format(mydic['Course name'], mydic['Course_Intro'], mydic['Course_syllabus'], mydic['Course_features'], mydic['Course_requirements'], mydic['Course_mentors'], mydic['Course_price']))

    except Exception as e:
        logging.info(e)

    else:
        logging.info('inside else')
        mydb.commit()
    finally:
        logging.info('inside finally')
        mydb.close()


# API
@app.route('/', methods=['GET'])
@cross_origin()
def home():
    return render_template('home.html')


# API
@app.route('/result', methods=['POST'])
@cross_origin()
def resultfunction():


    global mylist
    mylist = []
    courses_html = None
    courses = None
    beautiful_course_html = None

    try:
        if request.method == 'POST':
            search = get_course_name()
            formatted_search = search.upper().replace(" ", "-")
            search_link = "https://ineuron.ai/category/" + formatted_search
            logging.info(search_link)
            try:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")
                browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
                #browser = webdriver.Chrome(executable_path=r"C:\Users\Darshan\PycharmProjects\coursescraper\chromedriver.exe")
                browser.get(search_link)
                courses_html = browser.page_source
            except Exception as e:
                logging.info("Url Request Exception raised from", search_link, "\n" + str(e))

            try:
                beautiful_courses_html = BeautifulSoup(courses_html, 'html.parser')
                try:
                    courses = beautiful_courses_html.find_all("div", {"class": 'Course_course-card__f7WLr Course_card__rBLhD card'})
                    if not courses:
                        return render_template('noresults.html')
                except Exception as e:
                    logging.info('Exception raised during finding courses' + str(e))
            except Exception as e:
                logging.info('Exception raised during beautification of html code:' + str(e))

            for course in set(courses):
                course_name = []
                course_syllabus_name = []
                course_requirement_name = []
                course_mentor_name = []
                course_link = "https://ineuron.ai" + course.a['href']
                try:

                    browser.get(course_link)
                    course_html = browser.page_source

                    try:
                        beautiful_course_html = BeautifulSoup(course_html, 'html.parser')
                    except Exception as e:
                        logging.info('Exception raised during beautification of html code 2,' + str(e))
                except Exception as e:
                    logging.info('Url Request Exception raised from', course_link, '\n' + str(e))

                try:
                    logging.info('Finding price of' + course.a['href'])
                    price = beautiful_course_html.find_all('div', {'class': 'CoursePrice_price-block__DgFxJ CoursePrice_flex__Y4Ehc flex'})
                    price_text = price[0].span.text
                    logging.info('Price is:' + price_text)
                except Exception:
                    logging.info('Could not find price of course:' + course.a['href'])
                    price_text = 'Part of tech Neuron'

                try:
                    logging.info('Finding course_features of')
                    course_features = beautiful_course_html.find_all('div', {'class': 'CoursePrice_course-features__IBpSY'})
                    logging.info('Course features are:')
                    for i in course_features[0].ul:
                        course_name.append(i.text)
                        logging.info(i.text)
                except Exception:
                    logging.info('Could not find course features of course:' + course.a['href'])
                    course_name.append(' ')

                try:
                    logging.info('Finding course introduction' + course.a['href'])
                    course_about = beautiful_course_html.find_all('div', {'class': 'Hero_course-desc__lcACM'})
                    course_about_text = course_about[0].text
                    logging.info('Course introduction is:' + course_about_text)
                except Exception:
                    logging.info('Could not find course introduction of course:' + course.a['href'])
                    course_about_text = 'None'

                try:
                    logging.info('Finding course_syllabus of' + course.a['href'])
                    course_syllabus = beautiful_course_html.find_all('div', {'class': 'CourseLearning_card__0SWov card'})
                    logging.info('Course syllabus are:')
                    for i in course_syllabus[0].ul:
                        course_syllabus_name.append(i.text)
                        logging.info(i.text)
                except Exception:
                    logging.info('Could not find course syllabus of course:' + course.a['href'])
                    course_syllabus_name.append(' ')

                try:
                    logging.info('Finding course requirements of' + course.a['href'])
                    course_requirement = beautiful_course_html.find_all('div', {'class': 'CourseRequirement_card__lKmHf requirements card'})
                    logging.info('Course requirements are:')
                    for i in course_requirement[0].ul:
                        course_requirement_name.append(i.text)
                        logging.info(i.text)
                except Exception:
                    logging.info('Could not find course requirements of course:' + course.a['href'])
                    course_requirement_name.append(' ')

                try:
                    logging.info('Finding course mentor of' + course.a['href'])
                    course_mentor = beautiful_course_html.find_all('div', {'class': 'InstructorDetails_mentor__P07Cj InstructorDetails_card__mwVrB InstructorDetails_flex__g8BFa card flex'})
                    logging.info('Course mentors are:')
                    for i in range(len(course_mentor)):
                        course_mentor_name.append(course_mentor[i].div.h5.text)
                        logging.info(course_mentor[i].div.h5.text)
                except Exception:
                    logging.info('Could not find mentors of the course:' + course.a['href'])
                    course_mentor_name.append(' ')

                mydict = {'Course name': course.a['href'][8::1], 'Course_features': course_name, 'Course_price': price_text,
                          "Course_syllabus": course_syllabus_name, "Course_Intro": course_about_text,
                          "Course_requirements": course_requirement_name, "Course_mentors": course_mentor_name}

                mylist.append(mydict)

            browser.close()
            #insertdb()
            return render_template('results.html', mylist=mylist)

        else:
            logging.info('Method is not POST')

    except Exception as e:
        logging.info('Exception raised' + str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

