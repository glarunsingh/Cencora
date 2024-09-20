import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Observable, OperatorFunction } from 'rxjs';
import { debounceTime, distinctUntilChanged, map } from 'rxjs/operators';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { FeedbackModalComponent } from 'src/app/shared/modal/feedback-modal/feedback-modal.component';

@Component({
  selector: 'app-keyword-digest',
  templateUrl: './keyword-digest.component.html',
  styleUrls: ['./keyword-digest.component.scss']
})
export class KeywordDigestComponent {

  public model: any;
  public topKeywords: string[] = [];
  public keywordList: string[] = [];
  public keywordDigestRecords: any[] = [];
  public keywordDigestRecords_clone: any[] = [];
  public countWidgetResultsInput: any = [];

  timeStampsList: any[] = [];
  public selectedTimeFrame: string = "Past 180 days";

  public showTilesLoader: boolean = false;
  public showSummaryLoader: boolean = false;

  public showTilesBanner: boolean = false;
  public tilesBannerText: string = "";

  public showSummaryBanner: boolean = false;
  public summBannerText: string = "";

  public sentimentFilterList: any[] = [];
  public clientNamesFilterList: any[] = [];

  public appliedFiltersList: any[] = [];

  clientNamesFilterCountObj: any = { 'name': "Client names", total: 0 }
  sentimentFilterCountObj: any = { 'name': "Sentiment", total: 0 }
  maxLength: number = 200;
  public graph_details: any = {};
  public metaData: any = {};
  public keywordDigestTabs = ['News articles', 'Consolidated summary', 'Key insights', 'Market report'];
  public activeIndex: number = 0;
  public feedbackMap = new Map();
  public keywordSummaryObj: any = {};

  constructor(public apiService: ApiService, public commonService: CommonService,
    private changeDetector: ChangeDetectorRef, private modalService: NgbModal) { }

  ngOnInit() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.metaData = this.commonService.getStorageItems('metaData');
    this.getKeywordsData();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }


  getKeywordsData() {
    this.apiService.fetchKeywords({
      "user_email": this.graph_details['mail'],
      "department": this.metaData['department_name']
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.topKeywords = cbs['data']['top_keywords'];
          this.keywordList = cbs['data']['keywords']
          this.timeStampsList = [
            'Past 24 hours',
            'Past 48 hours',
            'Past week',
            'Past 3 weeks',
            'Past 180 days'
          ];
          this.activeIndex = 0;
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  search: OperatorFunction<string, readonly string[]> = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(200),
      distinctUntilChanged(),
      map((term) =>
        term.length < 2 ? [] : this.keywordList.filter((v) => v.toLowerCase().indexOf(term.toLowerCase()) > -1).slice(0, 10),
      ),
    );

  setTopKeyword(item: string) {
    this.model = item;
    this.keywordDigestData();
  }

  collectRadioButtonChange(event: any) {
    this.selectedTimeFrame = event;
    if (this.model == "" || this.model == undefined) {
      this.bannerHandler();
    } else {
      this.keywordDigestData();
    }
  }

  keywordDigestData() {
    this.clearAllFilters();
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame);
    let reqObj =
    {
      "search_text": this.model,
      "start_date": timeFrame.startDate, /**selected filter time frame date */
      "end_date": timeFrame.endDate, /**current date */
      "emp_id": this.graph_details['id'],
      "pageInformation": "keyword_digest-News Articles",
      "department": this.metaData['department_name']
    }
    this.showTilesBanner = false;
    if (reqObj['search_text'] && reqObj['start_date'] && reqObj['end_date']) {
      this.showTilesLoader = true;
      this.apiService.getKeywordSearchData(reqObj)
        .subscribe((cbs: any) => {
          if (cbs['status'] == "success") {
            this.tilesBannerText = "";
            let tempSearchData = this.commonService.modify_article_data(cbs['data']['news_articles']['search_data'].map((x: any) => ({ ...x, 'isActive': false })));
            this.manageClientFilters(cbs['data']['news_articles']);
            this.manageSentiments(cbs['data']['news_articles']);
            this.keywordDigestRecords = JSON.parse(JSON.stringify(tempSearchData));
            this.filterExistingResults();
          } else {
            this.showTilesBanner = true;
            this.tilesBannerText = cbs['message']
          }
          this.showTilesLoader = false;
        }, (cbe: HttpErrorResponse) => {
          this.showTilesLoader = false;
          console.error(cbe.message)
        })
      this.getSummaryFromModels();
    }
    else {
      this.showTilesBanner = false;
    }
    this.activeIndex = 0;
    this.commonService.scrollToTop();
  }

  getSummaryFromModels() {
    this.showSummaryBanner = false;
    this.showSummaryLoader = true;
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame);
    this.apiService.getKeywordSummary({
      "search_text": this.model,
      "start_date": timeFrame.startDate, /**selected filter time frame date */
      "end_date": timeFrame.endDate, /**current date */
      "department": this.metaData['department_name']
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.keywordSummaryObj = cbs['data'];
          this.summBannerText = "";
        }
        else {
          this.showSummaryBanner = true;
          this.summBannerText = cbs['message']
        }
        this.showSummaryLoader = false;
      }, (cbe: HttpErrorResponse) => {
        this.showSummaryLoader = false;
        console.error(cbe.message)
      })
  }

  manageClientFilters(response: any) {
    let tempclientNamesFilterList = response['client_list'].map((x: any) => {
      return ({
        'text': x,
        'isChecked': true
      })
    })
    tempclientNamesFilterList.unshift({ isChecked: false, text: 'All' });
    this.clientNamesFilterList = tempclientNamesFilterList;
    // Prepare selected client items
    const selectedClientItems = tempclientNamesFilterList.filter((item: any) => item.isChecked);
    // Call toggleCheckbox function with selected client items
    this.toggleCheckbox({ from: 'Client names', data: selectedClientItems });
    this.clientNamesFilterList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(this.clientNamesFilterList)))
  }

  manageSentiments(response: any) {
    let tempSentimentList = response['sentiment'].map((x: any) => {
      return ({
        'text': x,
        'isChecked': true
      })
    });
    tempSentimentList.unshift({ isChecked: false, text: 'All' });
    this.sentimentFilterList = tempSentimentList;
    // Prepare selected client items
    const selectedClientItems = tempSentimentList.filter((item: any) => item.isChecked);
    // Call toggleCheckbox function with selected client items
    this.toggleCheckbox({ from: 'Sentiment', data: selectedClientItems });
    this.sentimentFilterList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(this.sentimentFilterList)))
  }

  toggleCheckbox(item: { from: string, data: any[] }) {
    this.appliedFiltersList = this.commonService.createFilterItemsList(item);
    this.clientNamesFilterCountObj['total'] = this.appliedFiltersList.filter(x => x['from'] == "Client names").length;
    this.sentimentFilterCountObj['total'] = this.appliedFiltersList.filter(x => x['from'] == "Sentiment").length;
    this.filterExistingResults();
  }

  clearAllSelectedFilter(type: string) { /**clear all the applied filters on box cross icon click */
    if (type == "Client names") {
      this.clientNamesFilterList.map(x => x['isChecked'] = false);
      this.clientNamesFilterCountObj['total'] = 0;
      this.appliedFiltersList.map(x => {
        if (x['from'] == "Client names") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Client names')
    }
    else {
      this.sentimentFilterList.map(x => x['isChecked'] = false)
      this.sentimentFilterCountObj['total'] = 0;
      this.appliedFiltersList.map(x => {
        if (x['from'] == "Sentiment") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Sentiment')
    }
    this.filterExistingResults();
  }

  filterExistingResults() { /**runs on every client name and sentiment checkbox filtering */
    const response = JSON.parse(JSON.stringify(this.keywordDigestRecords));
    const clientNamesWithoutAll = this.clientNamesFilterList.filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']);
    const sentimentWithoutAll = this.sentimentFilterList.filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']);
    this.keywordDigestRecords_clone = response
      .filter((x: any) => {
        if (clientNamesWithoutAll.length && sentimentWithoutAll.length) {
          if (clientNamesWithoutAll.includes(x['client_name']) && sentimentWithoutAll.includes(x['sentiment'])) return true;
        }
        return false;
      }).map((item: any) => {
        if (this.feedbackMap.has(item['news_url'])) {
          const value = this.feedbackMap.get(item['news_url']);
          item['isThumbsUp'] = value['isThumbsUp'];
          item['isThumbsDown'] = value['isThumbsDown'];
        }
        return item
      });
    this.countWidgetResultsInput = [...this.keywordDigestRecords_clone].sort((a, b) => b['@search.score'] - a['@search.score'])
    this.activeIndex = 0;
  }

  showMore(index: number) {
    this.keywordDigestRecords_clone[index]['isActive'] = true;
  }

  showLess(index: number) {
    this.keywordDigestRecords_clone[index]['isActive'] = false;
  }

  callApi(): void { /**called on every search bar input change */
    this.keywordDigestData();
  }

  clearAllFilters(): void {
    this.sentimentFilterList = [];
    this.clientNamesFilterList = [];
    this.appliedFiltersList = [];
    this.countWidgetResultsInput = [];
    this.keywordDigestRecords = [];
    this.keywordDigestRecords_clone = [];
    this.clientNamesFilterCountObj = { 'name': "Client names", total: 0 }
    this.sentimentFilterCountObj = { 'name': "Sentiment", total: 0 }
    this.keywordSummaryObj = {};
    this.feedbackMap.clear();
  }

  bannerHandler() {
    this.showTilesBanner = true;
    this.tilesBannerText = "Type some keywords to fetch records..."
  }

  clearInputSearch() {
    this.model = "";
    this.clearAllFilters();
    this.bannerHandler();
  }

  collectSelectedCount(page: any) { /**filter records based on selected page in count widget dropdown */
    this.keywordDigestRecords_clone = this.countWidgetResultsInput.slice(0, page != "All" ? page : this.countWidgetResultsInput.length)
  }

  downloadClientNewsUpdate() {
    const reqObj = {
      "department": this.metaData['department_name'],
      "url_list": this.keywordDigestRecords_clone.map(x => x['news_url'])
    }
    this.apiService.downloadKeyworsDigestData(reqObj)
      .subscribe((cbs: any) => {
        const url = window.URL.createObjectURL(cbs);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Keyword_Digest_' + '' + this.commonService.getTimeStampFormat() + '.xlsx'; // Set the desired filename
        a.click();
        window.URL.revokeObjectURL(url);
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  collectThumbsupEvent(article: any) {
    let thumbsupObj = {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "pageInformation": "keyword_digest-News Articles",
      "search_query": this.model
    }
    const reqObj = { ...article, ...thumbsupObj };
    this.feedbackApiHandler(reqObj, (cbs: string) => {
      if (cbs == "success") {
        this.modifyFeedbackState(article, 'isThumbsUp', 'isThumbsDown');
      }
    });
  }

  collectThumbsDownEvent(article: any) {
    let thumbsDownObj = {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "pageInformation": "keyword_digest-News Articles",
      "search_query": this.model
    }
    const reqObj = { ...article, ...thumbsDownObj };
    if (article.isThumbsDown) {
      this.feedbackApiHandler(reqObj, (cbs: string) => {
        if (cbs == 'success') {
          this.modifyFeedbackState(article, 'isThumbsDown', 'isThumbsUp');
        }
      });
    }
    else {
      const feedbackModalRef = this.modalService.open(FeedbackModalComponent, { size: 'lg', backdrop: 'static', centered: true });
      feedbackModalRef.componentInstance.article = article;
      if (feedbackModalRef) {
        feedbackModalRef.closed.subscribe(resp => {
          if (resp) {
            reqObj['category'] = resp['category'];
            reqObj['comment'] = resp['comment']
            this.feedbackApiHandler(reqObj, (cbs: string) => {
              if (cbs == 'success') {
                this.modifyFeedbackState(article, 'isThumbsDown', 'isThumbsUp');
              }
            });
          }
        })
      }
    }
  }

  modifyFeedbackState(article: any, key1: string, key2: string) {
    this.keywordDigestRecords_clone = JSON.parse(JSON.stringify(this.keywordDigestRecords_clone.map((x: any) => {
      if (x['news_url'] == article.news_url) {
        x[key1] = !x[key1];
        if (x[key1]) x[key2] = false;
      };
      this.feedbackMap.set(x['news_url'], { 'isThumbsUp': x['isThumbsUp'], 'isThumbsDown': x['isThumbsDown'] })
      return x;
    })))
  }

  feedbackApiHandler(feedbackPayload: any, cbs: any) {
    delete feedbackPayload['isThumbsUp'];
    delete feedbackPayload['isThumbsDown'];
    this.showTilesBanner = false;
    this.apiService.updateFeedback(feedbackPayload)
      .subscribe((resp: any) => {
        if (resp['success'] == true) {
          cbs("success")
          this.showTilesBanner = true;
          this.tilesBannerText = resp['message']
        }
        else {
          this.showTilesBanner = true;
          this.tilesBannerText = resp['message']
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }


  changeTab(index: number) {
    this.activeIndex = index;
  }

}
