from flask import Flask
from flask import render_template
from flask import request
from flask import make_response
from flask import url_for
from datetime import datetime
from pymongo import MongoClient
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
tls.set_credentials_file(username='blazerchris', api_key='ugTyhlzkMrpCvhvUvOu9')

app = Flask(__name__)

client = MongoClient('localhost',27017)
db = client.yelp_lite
yelp_business = db.business
yelp_review = db.review
#yelp_checkin = db.checkin

neg_string = 'angry annoy anxious appalling atrocious awful bad banal boring broken cold cold-hearted collapse confused contradictory contrary corrupt  creepy cry dead damage damaging dastardly deplorable depressed deprived deformed deny despicable detrimental dirty disease disgusting disheveled dishonest dishonorable dismal distress dreadful dreary enraged eroding evil fail faulty fear feeble fight filthy foul frighten frightful enraged eroding evil fail faulty fear feeble fight filthy foul frighten frightful gawky ghastly grave greed grim grimace gross grotesque gruesome guilty haggard hard hard-hearted harmful hate hideous homely horrendous horrible hostile hurt hurtful icky ignore ignorant ill immature imperfect impossible inane inelegant infernal injure injurious insane insidious insipid jealous junky lose lousy lumpy malicious mean menacing messy misshapen missing misunderstood moan moldy monstrous naive nasty naughty negate negative never nobody nondescript nonsense noxious objectionable odious offensive old oppressive pain perturb pessimistic petty plain poisonous poor prejudice questionable quirky quit reject renege repellant reptilian repulsive repugnant revenge revolting rocky rotten rude ruthless sad savage scare scary scream severe shoddy shocking sick sickening sinister slimy smelly sobbing sorry spiteful sticky stinky stormy stressful stuck stupid substandard suspect suspicious tense terrible terrifying threatening ugly undermine unfair unfavorable unhappy unhealthy unjust unlucky unpleasant upset unsatisfactory unsightly untoward unwanted unwelcome unwholesome unwieldy unwise upset vice vicious vile villainous vindictive wary weary wicked woeful worthless wound yell yucky'
pos_string = 'adorable accepted accomplish accomplishment achievement admire affirmative amazing appealing attractive awesome brilliant celebrated certain champ champion charming cheery choice classic classical clean commend composed congratulation constant cool courageous creative cute dazzling delight delightful distinguished divine earnest easy ecstatic effective effervescent efficient effortless electrifying elegant enchanting encouraging endorsed energetic energized engaging enthusiastic essential esteemed ethical excellent exciting exquisite fabulous fair familiar famous fantastic favorable fetching fine fitting flourishing fortunate free fresh friendly fun funny generous genius genuine giving glamorous glowing good gorgeous graceful great green grin growing handsome happy harmonious healing healthy hearty heavenly honest honorable honored hug idea ideal imaginative imagine impressive independent innovate innovative instant instantaneous instinctive intuitive intellectual intelligent inventive jovial joy jubilant keen kind knowing knowledgeable laugh legendary light learned lively lovely lucid lucky luminous marvelous masterful meaningful merit meritorious miraculous motivating moving natural nice novel now nurturing nutritious okay one one-hundred percent open optimistic paradise perfect phenomenal pleasurable plentiful pleasant poised polished popular positive powerful prepared pretty principled productive progress prominent protected proud quality quick quiet ready reassuring refined refreshing rejoice reliable remarkable resounding respected restored reward rewarding right robust safe satisfactory secure seemly simple skilled skillful smile soulful sparkling special spirited spiritual stirring stupendous stunning success successful sunny super superb supporting surprising terrific thorough thrilling thriving tops tranquil transforming transformative trusting truthful unreal unwavering up upbeat upright upstanding valued vibrant victorious victory vigorous virtuous vital vivacious wealthy welcome well whole wholesome willing wonderful wondrous worthy wow yes yummy zeal zealous'

def get_restaurant(cuisine1,cuisine2,price):
    result = []
    if cuisine1 and cuisine2 == 'None':
        cursor = yelp_business.find({'categories' : cuisine1, 'attributes.Price Range' : price},{"_id":0,'type':0,'hours':0,'neighborhoods':0}).sort([["stars",-1],['review_count',-1]]).limit(5)
        for word in cursor:
            result.append(word)
            msg = 'Yes! We found what you are looking for!'
        if len(result) == 0:
            cursor = yelp_business.find({'categories' : cuisine1},{"_id":0,'type':0,'hours':0,'neighborhoods':0}).sort([["stars",-1],['review_count',-1]]).limit(5)
            for word in cursor:
                result.append(word)
            msg = "Sorry! We coundn't find what you are looing for. But here are our recommendations!"
    else:
        cursor = yelp_business.find({'$and' : [{'categories' : cuisine1}, {'categories' : cuisine2}, {'attributes.Price Range' : price}]},{"_id":0,'type':0,'hours':0,'neighborhoods':0}).sort([["stars",-1],['review_count',-1]]).limit(5)
        for word in cursor:
            result.append(word)
            msg = 'Yes! We found what you are looking for!'
        if len(result) == 0:
            cursor = yelp_business.find({'$and' : [{'$or': [{'categories' : cuisine1}, {'categories' : cuisine2}]}, {'attributes.Price Range' : {'$lte' : price}}]},{"_id":0,'type':0,'hours':0,'neighborhoods':0}).sort([["stars",-1],['review_count',-1]]).limit(5)
            for word in cursor:
                result.append(word)
                msg = "Sorry! We coundn't find what you are looing for. But here are our recommendations!"       
    return (msg,result) 

def get_buz_info(result):
    buz_info = {}
    buz_info['name'] = result[0].get('name')
    buz_info['address'] = result[0].get('full_address').replace('\n',', ')
    buz_info['lat'] = result[0].get('latitude')
    buz_info['lon'] = result[0].get('longitude')
    buz_info['buz_id'] = result[0].get('business_id')
    return buz_info

def recommended_location(result):
    lats = []
    lons = []
    names = []
    if len(result) > 1:
        for info in result[1:]:
            lats.append(info.get('latitude'))
            lons.append(info.get('longitude'))
            names.append(info.get('name'))
    return lats,lons,names

def get_buz_info(buz_id):
    info = {}
    cursor = yelp_business.find({"business_id" : buz_id})
    for word in cursor:
        info['name'] = word.get('name')
        info['address'] = word.get('full_address').replace('\n',', ')
    return info

def get_top_reviews(buz_id,stars):
    top_review = []
    cursor = yelp_review.find({'business_id' : buz_id,'stars' : stars}).sort([["votes.useful",-1]]).limit(35)
    for word in cursor:
        top_review.append(word.get('text'))
    return top_review

def get_top3_reviews(buz_id):
    top3_review = []
    cursor = yelp_review.find({'business_id' : buz_id}).sort([["votes.useful",-1]]).limit(3)
    for word in cursor:
        top3_review.append(word.get('text'))
    return top3_review

def get_season_rating(buz_id):
    # This function take a single business_id and return a list of average rating for each year each season
    #Format:
    #dict= {2006:(spring_rating,summer_rating,fall_rating,winter_rating),2007:(spring_rating,...),...}
    cursor = yelp_review.find({"business_id" : buz_id})
    messy = []
    for word in cursor:
        messy.append((word.get("date"),word.get("stars")))
    year = {}
    for d_s in messy:
        year.setdefault(d_s[0][0:4], []).append(d_s)
    season_rating = {}
    for k,v in year.items():
        spring = 0
        count_1 = 0
        summer = 0
        count_2 = 0
        fall = 0
        count_3 = 0
        winter = 0
        count_4 = 0
        for rating in year[k]:
            if 1 <= int(rating[0][5:7]) <= 3:
                spring = spring + int(rating[1])
                count_1 = count_1 + 1
            elif 4 <= int(rating[0][5:7]) <= 6:
                summer = summer + int(rating[1])
                count_2 = count_2 + 1
            elif 7 <= int(rating[0][5:7]) <= 9:
                fall = fall + int(rating[1])
                count_3 = count_3 + 1
            else:
                winter = winter + int(rating[1])
                count_4 = count_4 + 1
        if count_1 != 0:
            spring_rating = spring/count_1
        else:
            spring_rating = 0
        if count_2 != 0:
            summer_rating = summer/count_2
        else:
            summer_rating = 0
        if count_3 != 0:
            fall_rating = fall/count_3
        else:
            fall_rating = 0
        if count_4 != 0:
            winter_rating = winter/count_4
        else:
            winter_rating = 0
        season_rating[k] = (spring_rating,summer_rating,fall_rating,winter_rating)
    return season_rating

def plot_season(season_data):
    #Part 1 sort out data
    list_hist_values=list((season_data.values()))
    list_hist_keys=list((season_data.keys()))
    year_list=[]
    for year in list_hist_keys:
        year_list.append(int(year))
    years=sorted(year_list)
    new_values=list()
    for i in years:
        new_values.append(season_data[str(i)])
    new_spring_values=list()
    new_summer_values=[]
    new_fall_values=[]
    new_winter_values=[]
    for j in list(range(len(new_values))):
        new_spring_values.append(new_values[j][0])
    for k in list(range(len(new_values))):
        new_summer_values.append(new_values[k][1])
    for l in list(range(len(new_values))):
        new_fall_values.append(new_values[l][2])
    for m in list(range(len(new_values))):
        new_winter_values.append(new_values[m][3])
    weather_values=[new_spring_values,new_summer_values,new_fall_values,new_winter_values]
    #Part2 graph using plotly
    trace=list()
    name_list=['spring','summer','fall','winter']
    color_list=['rgb(0, 255, 127))','rgb(249,214,46)','rgb(219,167,46)','rgb(172,228,234)']
    trace0 = go.Bar(
        x=years,
        y=weather_values[0],
        name=name_list[0],
        marker=dict(
            color='rgb(0, 255, 127))'
        )
    )
    trace1 = go.Bar(
        x=years,
        y=weather_values[1],
        name=name_list[1],
        marker=dict(
            color='rgb(249,214,46)'
        )
    )
    trace2 = go.Bar(
        x=years,
        y=weather_values[2],
        name=name_list[2],
        marker=dict(
            color='rgb(219,167,46)'
        )
    )
    trace3 = go.Bar(
        x=years,
        y=weather_values[3],
        name=name_list[3],
        marker=dict(
            color='rgb(172,228,234)'
        )
    )
                 
    data=[trace0,trace1,trace2,trace3]
    layout = go.Layout(
        barmode='group')

    fig = go.Figure(data=data, layout=layout)
    py.iplot(fig, filename='season_bar')
    return None

def get_star_distribution(buz_id):
    star_distribution = []
    star_perc=[]
    star_freq=[]
    for i in range(5):
        star = i+1
        cursor = yelp_review.find({"business_id":buz_id,"stars":star}).count()
        star_distribution.append((star,cursor))
    for k in range(5):
        star_freq.append(star_distribution[k][1])
    for j in range(5):
        star_perc.append((star_freq[j]/sum(star_freq)*100))
    return star_perc

def get_pie_buz(buz_id):
    fig = {
        'data': [{'labels': ['1 star', '2 stars', '3 stars','4 stars','5 stars'],
                'values': get_star_distribution(buz_id),
                'type': 'pie'}],
        'layout': {'title': 'Ratings'}
        }

    py.iplot(fig,filename='star_distribution_buz')
    return None

def get_busy_data(buz_id):
    cursor = yelp_business.find({"business_id" : buz_id})
    rest_name=cursor[0]['name']
    cursor1=yelp_checkin.find({"business_id":buz_id})
    checkin_keys=(list(cursor1[0]['checkin_info']))
    x=(list(cursor1[0]['checkin_info'].keys()))
    y=(list(cursor1[0]['checkin_info'].values()))
    crowd_checkin=[]
    z=list(zip(x,y))   
    wk_d_list=[]
    hr_d_list=[]
    for wk_d in list(range(len(checkin_keys))):
        wk_d_list.append(z[wk_d][0][-1:])
        hr_d_list.append(z[wk_d][0][:-2])
    m=[0,1,2,3,4,5,6]
    Monday_list=[]
    Tuesday_list=[]
    Wednesday_list=[]
    Thursday_list=[]
    Friday_list=[]
    Saturday_list=[]
    Sunday_list=[]
    hm_list=[]
    ht_list=[]
    hw_list=[]
    hth_list=[]
    hf_list=[]
    hs_list=[]
    hsu_list=[]
    main_tuple=list(zip(wk_d_list,hr_d_list,y))
    for n in (list(range(len(checkin_keys)))):
        if int(main_tuple[n][0])==0:
            Monday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            hm_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==1:
            Tuesday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            ht_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==2:
            Wednesday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            hw_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==3:
            Thursday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            hth_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==4:
            Friday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            hf_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==5:
            Saturday_list.append((int(main_tuple[n][1]),main_tuple[n][2]))
            hs_list.append(int(main_tuple[n][1]))
        elif int(main_tuple[n][0])==6:
            Sunday_list.append((int(main_tuple[n][1]),main_tuple[n][2])) 
            hsu_list.append(int(main_tuple[n][1]))
    for hours in list(range(24)):
        if hours not in hm_list:
            Monday_list.append((hours,0))
        if hours not in ht_list:
            Tuesday_list.append((hours,0))
        if hours not in hw_list:
            Wednesday_list.append((hours,0))
        if hours not in hth_list:
            Thursday_list.append((hours,0))
        if hours not in hf_list:
            Friday_list.append((hours,0))
        if hours not in hs_list:
            Saturday_list.append((hours,0))
        if hours not in hsu_list:
            Sunday_list.append((hours,0))
    mon_crowd=[]
    tues_crowd=[]
    wed_crowd=[]
    thu_crowd=[]
    fri_crowd=[]
    sat_crowd=[]
    sun_crowd=[]
    for crowd in list(range(24)):
        mon_crowd.append(sorted(Monday_list)[crowd][1])
        tues_crowd.append(sorted(Tuesday_list)[crowd][1])
        wed_crowd.append(sorted(Wednesday_list)[crowd][1])
        thu_crowd.append(sorted(Thursday_list)[crowd][1])
        fri_crowd.append(sorted(Friday_list)[crowd][1])
        sat_crowd.append(sorted(Saturday_list)[crowd][1])
        sun_crowd.append(sorted(Sunday_list)[crowd][1])
    return mon_crowd,tues_crowd,wed_crowd,thu_crowd,fri_crowd,sat_crowd,sun_crowd,rest_name

def get_busy_graph(buz_id):
    import datetime as dt
    hours = [ dt.time(i).strftime('%I %p') for i in range(24)]
    import calendar
    my_date = dt.date.today()
    this_day=calendar.day_name[my_date.weekday()]
    if this_day=='Monday':
        d=get_busy_data(buz_id)[0]
    if this_day=='Tuesday':
        d=get_busy_data(buz_id)[1]
    if this_day=='Wednesday':
        d=get_busy_data(buz_id)[2]
    if this_day=='Thursday':
        d=get_busy_data(buz_id)[3]
    if this_day=='Friday':
        d=get_busy_data(buz_id)[4]
    if this_day=='Saturday':
        d=get_busy_data(buz_id)[5]
    if this_day=='Sunday':
        d=get_busy_data(buz_id)[6]
    trace0 = go.Bar(
        x=hours,
        y=d,
        name=this_day,
        marker=dict(
            color='rgb(150,246,66)'
        )
    )
        
    data=[trace0]
    layout = go.Layout(
        title=this_day,
        xaxis=dict(tickangle=-45),
        barmode='group')
    fig = go.Figure(data=data, layout=layout)
    py.iplot(fig, filename='busy_chart')
    return None

def get_corpus_1(reviews,stars,pos_string,neg_string):
    from wordcloud import STOPWORDS
    addition_words = ["across","also","though","yeah","_http","http","http_www"]
    stopwords = list(STOPWORDS)
    stopwords.extend(addition_words)
    if stars == 1:
        pos_word = pos_string.split(' ')
        stopwords.extend(pos_word)
    elif stars == 5:
        neg_word = neg_string.split(' ')
        stopwords.extend(neg_word)
    final_stopwords = set(stopwords[1:])
    import re
    delete_sym = ['\n\n','\n','....','...','..',"/","-",":"]
    clean = []
    for rev in reviews:
        rev = re.sub('[$!?*]', '',rev)
        rev = re.sub(r'\([^)]*\)', '', rev)
        rev = rev.replace('"',"'")
        rev = rev.replace("\\","")
        for sym in delete_sym:
            rev = rev.replace(sym,' ')
        clean.append(rev.split('.'))
    final = []
    for summary in clean:
        temp_list = []
        for sen in summary:
            half = sen.split(',')
            for word in half:
                temp_list.append(list(filter(None, word.split(' '))))
        temp_list = list(filter(None,temp_list))
        for breaks in temp_list:
            if len(breaks) == 1 and breaks[0] not in final_stopwords:
                final.append(breaks[0])
            elif 2 <= len(breaks) <= 3:
                final.append('_'.join(breaks))
            else:
                for i in range(len(breaks)-2):
                    if len(breaks[i+2]) > 3 and len(breaks[i]) > 2 and len(breaks[i+1]) >= 2 and breaks[i] not in final_stopwords:
                        final.append('_'.join([breaks[i],breaks[i+1],breaks[i+2]]))
    #corpus = ' '.join(final)
    import nltk
    from nltk.corpus import wordnet as wn
    list_new = []
    for word in final:
        temp_list = word.split("_")
        if len(temp_list)>1:
            temp_word1 = temp_list[-1]
            temp_word2 = temp_list[0]
            if temp_word2 == 'http':
                pass
            else:
                tmp1 = wn.synsets(temp_word1)
                tmp2 = wn.synsets(temp_word2)
                if tmp1!=[] and tmp2!=[]:
                    if tmp1[0].pos() == 's':
                        pass
                    else:
                        list_new.append(word)
                else:
                    pass

        else:
            if wn.synsets(word) == []:
                pass
            elif wn.synsets(word)[0].pos() == 'r':
                pass
            else:
                list_new.append(word)
    corpus = " ".join(list_new)
    return corpus

def get_wordcloud_png(pos,neg,buz_id):
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
    import wordcloud as wc
    thumbsup_mask = np.array(Image.open("C:/Users/Chris/Desktop/Yelp_Project_Folder/thumbsup_mask.png"))
    thumbsdown_mask = np.array(Image.open("C:/Users/Chris/Desktop/Yelp_Project_Folder/thumbsdown_mask.png"))
    wc_pos = wc.WordCloud(background_color="white", max_words=80, mask=thumbsup_mask, color_func=wc.get_single_color_func('green'))
    wc_neg = wc.WordCloud(background_color="white", max_words=80, mask=thumbsdown_mask, color_func=wc.get_single_color_func('red'))

    wc_pos.generate(pos)
    wc_neg.generate(neg)
    # store to file
    pos_img = ''.join([buz_id,"pos_wordcloud.png"])
    neg_img = ''.join([buz_id,"neg_wordcloud.png"])
    pos_path = ''.join(["C:/Users/Chris/Desktop/Yelp_Project_Folder/static/",pos_img])
    neg_path = ''.join(["C:/Users/Chris/Desktop/Yelp_Project_Folder/static/",neg_img])
    wc_pos.to_file(pos_path)
    wc_neg.to_file(neg_path)
    pname = [pos_img,neg_img]
    return pname


@app.route('/')
def index():
    return render_template("home.html")

@app.route('/results',methods = ['GET','POST'])
def restaurant():
	cuisine1 = request.form['Cuisine1']
	cuisine2 = request.form['Cuisine2']
	price = request.form['Price']
	msg,results = get_restaurant(cuisine1,cuisine2,price)
	buz_info = get_buz_info(results)
	lats,lons,names = recommended_location(results)
	buz_id = buz_info.get('buz_id')
	pos_review = get_top_reviews(buz_id,5)
	neg_review = get_top_reviews(buz_id,1)
    top3_review = get_top3_reviews(buz_id)
    season_rating = get_season_rating(buz_id)
    plot_season(season_rating)
    get_pie_buz(buz_id)
    get_busy_graph(get_id)
    pos_corpus = get_corpus_1(pos_reviews,5,pos_string,neg_string)
    neg_corpus = get_corpus_1(neg_reviews,1,pos_string,neg_string)
    pname = get_wordcloud_png(pos_corpus,neg_corpus,get_id)
	return render_template('results.html',result=lats)




if __name__ == "__main__":
    app.run()