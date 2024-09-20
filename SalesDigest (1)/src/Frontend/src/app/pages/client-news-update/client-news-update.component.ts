import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { FeedbackModalComponent } from 'src/app/shared/modal/feedback-modal/feedback-modal.component';

@Component({
  selector: 'app-client-news-update',
  templateUrl: './client-news-update.component.html',
  styleUrls: ['./client-news-update.component.scss']
})
export class ClientNewsUpdateComponent {

  timeStampsList: any[] = [
    'Past 24 hours',
    'Past 48 hours',
    'Past week',
    'Past 3 weeks',
    'Past 180 days'
  ]

  public selectedTimeFrame: string = "Past 3 weeks";

  sourceList: any[] = [];
  categoryList: any[] = [];
  clientNamesList: any[] = [];

  public clientNewsList: any[] = [];
  public sentimentList: any[] = [];
  public clientNewsList_clone: any[] = [];
  public countWidgetResultsInput: any[] = [];
  public appliedFiltersList: any[] = [];
  maxLength: number = 200;
  public showLoading: boolean = false;
  public showBanner: boolean = false;
  public bannerText: string = "";

  clientNamesFilterCountObj: any = { 'name': "Client names", total: 0 }
  sourceNamesFilterCountObj: any = { 'name': "Source", total: 0 }
  sentimentFilterCountObj: any = { 'name': "Sentiment", total: 0 }

  public graph_details: any = {};

  selectedTimestamps: { [key: string]: boolean } = {}; // Object to store selected timestampstoggleCheckbox(item: string) {

  constructor(public commonService: CommonService,
    private changeDetector: ChangeDetectorRef,
    public apiService: ApiService,
    private modalService: NgbModal) {
  }

  ngOnInit() {
    this.getFiltersData();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }

  getFiltersData() {
    const metaData = this.commonService.getStorageItems('metaData');
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.apiService.getClientNewsClientList({
      "user_email": this.graph_details['mail'],
      "department": metaData['department_name'],
      "client_specific": true
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.showBanner = false;
          cbs['data']['client'] = [...new Map(cbs['data']['client'].map((item: any) => [item['name'], item])).values()]
          cbs['data']['sourceList'] = [...new Map(cbs['data']['sourceList'].map((item: any) => [item['name'], item])).values()]
          if (cbs['data']['client'].length && cbs['data']['sourceList'].length) {
            this.manageClientFilters(cbs);
            this.manageSourceFilters(cbs);
            this.manageSentimentsFilters({ data: { sentiment: [{ 'name': 'Positive' }, { 'name': 'Negative' }, { 'name': 'Neutral' }] } });
          }
        }
        else {
          this.showBanner = true;
          this.bannerText = "No client list  or source list available"
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  manageClientFilters(response: any) {
    this.categoryList = [];
    // Process clientList
    const tempClientList = this.transformList(response.data.client, 'name')
    const isFavouriteExists = tempClientList.some((item: any) => item.isFavourite);

    if (!isFavouriteExists) {
      // tempClientList[0].isChecked = true; /**previously only zeroth item was checked not all  */
      tempClientList.map(x => x['isChecked'] = true) /**if no fav is available then make all as checked */
    } else {
      tempClientList.forEach((item: any) => {
        if (item.isFavourite) item.isChecked = true;
      });
      this.categoryList.push({ isChecked: true, text: 'Favorites' })
    }

    tempClientList.unshift({ isChecked: false, text: 'All' });
    this.clientNamesList = tempClientList;
    // Prepare selected client items
    const selectedClientItems = tempClientList.filter((item: any) => item.isChecked);
    // Call toggleCheckbox function with selected client items
    this.toggleCheckbox({ from: 'Client names', data: selectedClientItems });
    this.clientNamesList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(tempClientList)))
  }

  manageSourceFilters(response: any) {
    this.sourceList = [];
    // Process sourceList
    const sourceList = this.transformList(response.data.sourceList, 'name');
    sourceList.map(x => {
      if ((['Bing News', 'Bing', 'News Bing'].map(x => x.toLocaleLowerCase()).includes(x['text'].toLowerCase()) ||
        (['Becker Hospital Review', 'Becker Review Hospital', 'Becker Hospital'].map(x => x.toLocaleLowerCase()).includes(x['text'].toLowerCase())))) {
        x['isChecked'] = true
      }
    });
    sourceList.unshift({ isChecked: false, text: 'All' });
    this.sourceList = sourceList;
    // Call toggleCheckbox function with selected source items
    this.toggleCheckbox({ from: 'Source', data: sourceList });
    this.sourceList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(sourceList)))
  }

  manageSentimentsFilters(response: any) {
    this.sentimentList = [];
    // Process sentimentList
    const sentimentFilters = this.transformList(response.data.sentiment, 'name');
    sentimentFilters.map(x => x['isChecked'] = true) /**if no fav is available then make all as checked */
    sentimentFilters.unshift({ isChecked: false, text: 'All' });
    this.sentimentList = sentimentFilters
    // Call toggleCheckbox function with selected sentiment items
    this.toggleCheckbox({ from: 'Sentiment', data: sentimentFilters });
    this.sentimentList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(sentimentFilters)));
  }

  transformList = (list: any[], textKey: string): any[] => {
    return list.map((item: any) => ({
      ...item,
      isChecked: false,
      text: item[textKey],  // Rename 'name' to 'text'
    }));
  };

  collectRadioButtonChange(event: string) {
    this.selectedTimeFrame = event;
    this.getClientNewsUpdate();
  }

  toggleCheckbox(item: { from: string, data: any[] }) {
    this.appliedFiltersList = this.commonService.createFilterItemsList(item);
    this.clientNamesFilterCountObj['total'] = this.appliedFiltersList.filter((x: any) => x['from'] == "Client names").length;
    this.sourceNamesFilterCountObj['total'] = this.appliedFiltersList.filter(x => x['from'] == "Source").length;
    this.sentimentFilterCountObj['total'] = this.appliedFiltersList.filter(x => x['from'] == 'Sentiment').length;
    this.uncheckFavorites();
    this.getClientNewsUpdate();
  }

  uncheckFavorites() { /**check and uncheck favourite checkbox by client names selection */
    //check if all is selected in client names list
    const allClientChecked = this.clientNamesList.find(x => x['text'] == "All" && x['isChecked']);

    //check if favorites are checked
    const anyFavouritesChecked = this.clientNamesList.some(x => x['isFavourite'] && x['isChecked']);

    //check if any other items are checked
    const anyOtherChecked = this.clientNamesList.some(x => x['text'] != 'All' && x['isFavourite'] == false && x['isChecked']);

    if (allClientChecked) {
      this.categoryList = [{ isChecked: false, text: 'Favorites' }]
    }
    else if (anyFavouritesChecked && !anyOtherChecked) {
      this.categoryList = [{ isChecked: true, text: 'Favorites' }]
    } else {
      this.categoryList = [{ isChecked: false, text: 'Favorites' }]
    }
  }

  clientFavouriteHandler(item: { from: string, data: any[] }) { /**favorite checkbox handler */
    if (item?.data[0]?.isChecked) {
      this.clientNamesList.map(x => {
        if (x.isFavourite) x.isChecked = true;
        else x.isChecked = false;
      });
    } else {
      this.clientNamesList.map(x => {
        if (x.isFavourite) x.isChecked = false;
      });
    }
    this.toggleCheckbox({ from: 'Client names', data: this.clientNamesList });
  }

  clearAllSelectedFilter(type: string) { /**clear all the applied filters on box cross icon click */
    if (type == "Client names") {
      this.clientNamesList.map(x => x['isChecked'] = false);
      this.clientNamesFilterCountObj['total'] = 0;
      this.appliedFiltersList.map(x => {
        if (x['from'] == "Client names") x['isChecked'] = false;
      })
      this.categoryList = [{ isChecked: false, text: 'Favorites' }];
      this.commonService.updateMapByKey('Client names')
    }
    if (type == 'Source') {
      this.sourceList.map(x => x['isChecked'] = false)
      this.sourceNamesFilterCountObj['total'] = 0;
      this.appliedFiltersList.map(x => {
        if (x['from'] == "Source") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Source')
    }
    if (type == 'Sentiment') {
      this.sentimentList.map(x => x['isChecked'] = false)
      this.sentimentFilterCountObj['total'] = 0;
      this.appliedFiltersList.map(x => {
        if (x['from'] == "Sentiment") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Sentiment')
    }
    this.getClientNewsUpdate();
  }

  getClientNewsUpdate() {
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame);
    this.clientNewsList = [];
    this.clientNewsList_clone = [];
    let reqObj =
    {
      "source_name": this.sourceList.filter(x => x['isChecked']).filter(x => x['text'] != 'All').map(x => x['text']),
      "client": this.clientNamesList.filter(x => x['isChecked']).filter(x => x['text'] != 'All').map(x => x['text']),
      "sentiment_list": this.sentimentList.filter(x => x['isChecked']).filter(x => x['text'] != 'All').map(x => x['text']),
      "start_date": timeFrame.startDate, /**selected filter time frame date */
      "end_date": timeFrame.endDate, /**current date */
      "emp_id": this.graph_details['id'],
      pageInformation: "client-news-digest"
    }
    this.showBanner = false;
    if (reqObj.source_name.length && reqObj.client.length && reqObj.sentiment_list.length) {
      this.showLoading = true;
      this.apiService.getClientNewsUpdateData(reqObj)
        .subscribe((cbs: any) => {
          if (cbs['status'] == "success") {
            this.clientNewsList = this.commonService.modify_article_data(cbs['data']
              .map((x: any) => ({ ...x, 'isActive': false })));
            this.clientNewsList_clone = JSON.parse(JSON.stringify(this.clientNewsList))
            this.countWidgetResultsInput = [...this.clientNewsList_clone]
            this.showBanner = false;
          } else {
            this.showBanner = true;
            this.bannerText = cbs['message']
          }
          this.showLoading = false;
        }, (cbe: HttpErrorResponse) => {
          this.showLoading = false;
          this.showBanner = false;
          console.error(cbe.message)
        })
    }
    else {
      this.showBanner = true;
      this.bannerText = "No matching results were found!!. Please refine your search"
    }
    this.commonService.scrollToTop()
  }

  collectSelectedCount(page: any) {
    // const { resultInfoText, filteredByItemsList } = event;
    // this.countWidgetResultsInput = JSON.parse(JSON.stringify(filteredByItemsList))
    this.clientNewsList_clone = this.countWidgetResultsInput.slice(0, page != "All" ? page : this.countWidgetResultsInput.length)
  }

  showMore(index: number) {
    this.clientNewsList_clone[index]['isActive'] = true;
  }

  showLess(index: number) {
    this.clientNewsList_clone[index]['isActive'] = false;
  }

  downloadClientNewsUpdate() {
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame)
    let reqObj =
    {
      "source_name": this.sourceList.filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "client": this.clientNamesList.filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "sentiment_list": this.sentimentList.filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "start_date": timeFrame.startDate,
      "end_date": timeFrame.endDate
    }
    this.apiService.downloadClientNewsData(reqObj)
      .subscribe((cbs: any) => {
        const url = window.URL.createObjectURL(cbs);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Client_News_Update_' + '' + this.commonService.getTimeStampFormat() + '.xlsx'; // Set the desired filename
        a.click();
        window.URL.revokeObjectURL(url);
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  // thumbsUpHandler(article: any) {
  //   let reqObj = {
  //     news_url: article.news_url,
  //     "emp_id": this.graph_details['id'],
  //     "first_name": this.graph_details['givenName'],
  //     "last_name": this.graph_details['surname'],
  //     feedback: 'isThumbsUp',
  //     value: !article['isThumbsUp'],
  //     category: "",
  //     comment: "",
  //     pageInformation: "client-news-digest"
  //   }
  //   this.feedbackApiHandler(reqObj, (cbs: string) => {
  //     if (cbs == "success") {
  //       this.modifyFeedbackState(article, 'isThumbsUp', 'isThumbsDown');
  //     }
  //   });
  // }

  // thumbsDownHandler(article: any) {
  //   let reqObj = {
  //     news_url: article.news_url,
  //     "emp_id": this.graph_details['id'],
  //     "first_name": this.graph_details['givenName'],
  //     "last_name": this.graph_details['surname'],
  //     feedback: 'isThumbsDown',
  //     value: !article['isThumbsDown'],
  //     category: "",
  //     comment: "",
  //     pageInformation: "client-news-digest"
  //   }
  //   if (article.isThumbsDown) {
  //     this.feedbackApiHandler(reqObj, (cbs: string) => {
  //       if (cbs == 'success') {
  //         this.modifyFeedbackState(article, 'isThumbsDown', 'isThumbsUp');
  //       }
  //     });
  //   }
  //   else {
  //     const feedbackModalRef = this.modalService.open(FeedbackModalComponent, { size: 'lg', backdrop: 'static', centered: true });
  //     feedbackModalRef.componentInstance.article = article;
  //     if (feedbackModalRef) {
  //       feedbackModalRef.closed.subscribe(resp => {
  //         if (resp) {
  //           reqObj['category'] = resp['category'];
  //           reqObj['comment'] = resp['comment']
  //           this.feedbackApiHandler(reqObj, (cbs: string) => {
  //             if (cbs == 'success') {
  //               this.modifyFeedbackState(article, 'isThumbsDown', 'isThumbsUp');
  //             }
  //           });
  //         }
  //       })
  //     }
  //   }
  // }

  collectThumbsupEvent(article: any) {
    let thumbsupObj = {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      pageInformation: "client-news-digest"
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
      pageInformation: "client-news-digest"
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
    this.clientNewsList_clone = JSON.parse(JSON.stringify(this.clientNewsList_clone.map((x: any) => {
      if (x['news_url'] == article.news_url) {
        x[key1] = !x[key1];
        if (x[key1]) x[key2] = false;
      };
      return x;
    })))
  }

  feedbackApiHandler(feedbackPayload: any, cbs: any) {
    delete feedbackPayload['isThumbsUp'];
    delete feedbackPayload['isThumbsDown'];
    this.showBanner = false;
    this.apiService.updateFeedback(feedbackPayload)
      .subscribe((resp: any) => {
        if (resp['success'] == true) {
          cbs("success")
          this.showBanner = true;
          this.bannerText = resp['message']
        }
        else {
          this.showBanner = true;
          this.bannerText = cbs['message']
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }


  ngOnDestroy() {
    this.commonService.clearFilters();
  }



}
