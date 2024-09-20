import { Injectable } from '@angular/core';
import * as moment from 'moment';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CommonService {

  public selectedFiltersListMap = new Map();
  public selectedFiltersList: any[] = [];

  private user_graph_details = new BehaviorSubject<any>({});
  castUserGraphDetails = this.user_graph_details.asObservable();

  constructor() { }

  setStorageItems(key: string, value: any) {
    localStorage.setItem(key, value);
    if (key == "graph_details") this.user_graph_details.next(value);
  }

  getStorageItems(key: string) {
    const getLocalItem = localStorage.getItem(key);
    if (getLocalItem) {
      return JSON.parse(localStorage.getItem(key) || "")
    }
  }

  createFilterItemsList(item: any) {
    this.selectedFiltersListMap.set(item['from'], item['data'])
    this.selectedFiltersList = [];
    for (var [key, value] of this.selectedFiltersListMap) {
      value = value.map((x: any) => ({ ...x, 'from': key }))
      this.selectedFiltersList.push(...value);
    }
    this.selectedFiltersList = Array.from(new Map(this.selectedFiltersList.filter(x => x['isChecked'] == true).map(e => [e.text, e])).values());
    return this.selectedFiltersList
  }

  removeFiltersFromList(index: number) {
    this.selectedFiltersList = this.selectedFiltersList.filter((item, ind) => ind != index)
    return this.selectedFiltersList;
  }

  clearFilters() {
    this.selectedFiltersList = [];
    this.selectedFiltersListMap.clear();
  }

  updateMapByKey(args: string) {
    this.selectedFiltersListMap.get(args).map((x: any) => x['isChecked'] = false);
  }

  getSentimentBtnCls(sentiment_type: string): any {
    switch (sentiment_type) {
      case "Neutral":
      case "neutral":
        return 'btn cust-sentiment-btn-neutral'
      case "Positive":
      case "positive":
        return 'btn cust-sentiment-btn-positive'
      case "Negative":
      case "negative":
        return 'btn cust-sentiment-btn-negative'
      default:
        return 'btn cust-sentiment-btn-neutral'
    }
  }

  getLastSixMonths() {
    const today = new Date();
    let lastSixMonths = []

    for (var i = 5; i >= 0; i -= 1) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
      lastSixMonths.push(moment(date).format("MMMM YYYY"))
    }

    return lastSixMonths.reverse() // Result
  }

  formatTimFrameDates(appliedFiltersList: any[]) {
    return appliedFiltersList.map(obj => {
      return moment(new Date(obj['text'])).format("YYYY-MM");
    })
  }

  getTimeStampFormat() {
    return moment(new Date()).format("YYYYMMDHHmmss");
  }

  goToLink(url: string) {
    window.open(url, "_blank");
  }

  copyUrl(url: string) {
    navigator.clipboard.writeText(url);
  }

  modifySentimentTitleCase(sentiment: string) {
    return sentiment[0].toUpperCase() + sentiment.substr(1).toLowerCase();
  }

  manageAllCheckOption(list: any[]) {
    const allIClienttemsChecked = list?.filter(item => item['text'] != 'All').every(item => item.isChecked)
    if (list && list.length) list.find(item => item['text'] == "All").isChecked = allIClienttemsChecked;
    return list;
  }

  getStartEndDates(args: string) {
    let startDate: any = "";
    let endDate = moment(new Date()).format("YYYY-MM-DD");
    switch (args) {
      case 'Past 24 hours':
        startDate = moment().subtract(24, 'hours').format("YYYY-MM-DD");
        break;
      case 'Past 48 hours':
        startDate = moment().subtract(48, 'hours').format("YYYY-MM-DD");
        break;
      case 'Past week':
      case 'Past 1 week':
        startDate = moment().subtract(7, 'days').format("YYYY-MM-DD");
        break;
      case 'Past 3 weeks':
        startDate = moment().subtract(3, 'weeks').format("YYYY-MM-DD");
        break;
      case 'Past 5 weeks':
        startDate = moment().subtract(5, 'weeks').format("YYYY-MM-DD");
        break;
      case 'Past 180 days':
        startDate = moment().subtract(180, 'days').format("YYYY-MM-DD");
        break;
    }
    return { startDate, endDate }
  }

  modifyNewsDate(args: string, dateFormat: any) {
    return moment(new Date(args)).format(dateFormat)
  }

  modify_article_data(newsList: any) {
    return newsList.map((x: any) => ({
      ...x,
      favIcon: 'http://www.google.com/s2/favicons?domain=' + `${x.news_url}`,
    }));
  }

  uncheckAllOptionInFilters(argsList: any[], uncheckedItem: string) {
    argsList.map(x => {
      if (x['text'] == uncheckedItem) x['isChecked'] = false;
      if (x['text'] == "All") x['isChecked'] = false;
      return x;
    });
    return argsList
  }

  scrollToTop() {
    const ele = document.getElementById('container');
    ele?.scrollIntoView({behavior:'smooth',inline:'start'})
  }

}
