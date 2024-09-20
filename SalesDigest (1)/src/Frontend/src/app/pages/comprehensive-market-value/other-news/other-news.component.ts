import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { FeedbackModalComponent } from 'src/app/shared/modal/feedback-modal/feedback-modal.component';


@Component({
  selector: 'app-other-news',
  templateUrl: './other-news.component.html',
  styleUrls: ['./other-news.component.scss']
})
export class OtherNewsComponent {

  @Output() emitClearAllFilters = new EventEmitter();
  @Input() selectedTimeFrame: string | any;
  @Input() appliedSourcesList!: any[];

  public drugChannelList: any[] = [];
  public drugChannelDisplayList: any[] = [];
  public lastSixMonthsList: any[] = [];
  public countWidgetResultsInput: any[] = [];
  maxLength: number = 200;
  public showLoading: boolean = false;
  public showBanner: boolean = false;
  public bannerText: string = "";
  public graph_details: any = {};

  @Input() sourceNamesFilterCountObj: any
  @Input() sentimentFilterCountObj: any

  constructor(public commonService: CommonService, private apiService: ApiService,
    private modalService: NgbModal) {
  }

  ngOnInit() {
    this.getDrugChannelData();
  }

  ngOnChanges() {
    this.getDrugChannelData();
  }

  showMore(index: number) {
    this.drugChannelDisplayList[index]['isActive'] = true;
  }

  showLess(index: number) {
    this.drugChannelDisplayList[index]['isActive'] = false;
  }

  clearAllSelectedFilter(args: string) {
    this.emitClearAllFilters.emit(args)
    this.getDrugChannelData();
  }

  collectFilteredItems(event: any) {
    const { resultInfoText, filteredByItemsList } = event;
    this.drugChannelDisplayList = JSON.parse(JSON.stringify(filteredByItemsList))
  }

  getDrugChannelData() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.drugChannelList = [];
    this.drugChannelDisplayList = [];
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame)
    let reqObj =
    {
      "source_name": this.appliedSourcesList.filter(x => x['from'] == 'Source').filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "sentiment_list": this.appliedSourcesList.filter(x => x['from'] == 'Sentiment').filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "client": [""],
      "start_date": timeFrame.startDate, /**selected filter time frame date */
      "end_date": timeFrame.endDate, /**current date */
      "emp_id": this.graph_details['id'],
      pageInformation: "comprehensive-value"
    }
    this.showBanner = false;
    if (reqObj.source_name.length && reqObj.sentiment_list.length) {
      this.showLoading = true
      this.apiService.getClientNewsUpdateData(reqObj)
        .subscribe((cbs: any) => {
          if (cbs['status'] == "success") {
            this.drugChannelList = this.commonService.modify_article_data(cbs['data']
              .map((x: any) => ({ ...x, 'isActive': false })));
            this.drugChannelDisplayList = JSON.parse(JSON.stringify(this.drugChannelList))
            this.countWidgetResultsInput = [...this.drugChannelDisplayList]
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
    this.drugChannelDisplayList = this.countWidgetResultsInput.slice(0, page != "All" ? page : this.countWidgetResultsInput.length)
  }

  downloadOtherNews() {
    const timeFrame = this.commonService.getStartEndDates(this.selectedTimeFrame)
    let reqObj =
    {
      "source_name": this.appliedSourcesList.filter(x => x['from'] == 'Source').filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "sentiment_list": this.appliedSourcesList.filter(x => x['from'] == 'Sentiment').filter(x => x['text'] != 'All' && x['isChecked']).map(x => x['text']),
      "client": [""],
      "start_date": timeFrame.startDate,
      "end_date": timeFrame.endDate
    }
    this.apiService.downloadDrugChannelData(reqObj)
      .subscribe((cbs: any) => {
        const url = window.URL.createObjectURL(cbs);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Other_News_' + '' + this.commonService.getTimeStampFormat() + '.xlsx'; // Set the desired filename
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
  //     pageInformation: "comprehensive-value"
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
  //     pageInformation: "comprehensive-value"
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

  // modifyFeedbackState(article: any, key1: string, key2: string) {
  //   this.drugChannelDisplayList.map((x: any) => {
  //     if (x['news_url'] == article.news_url) {
  //       x[key1] = !x[key1];
  //       if (x[key1]) x[key2] = false;
  //     };
  //   })
  // }

  collectThumbsupEvent(article: any) {
    let thumbsupObj = {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      pageInformation: "comprehensive-value"
    }
    const reqObj = { ...article, ...thumbsupObj };
    this.feedbackApiHandler(reqObj, (cbs: string) => {
      if (cbs == "success") {
        this.modifyFeedbackState(article, 'isThumbsUp', 'isThumbsDown')
      }
    });
  }

  collectThumbsDownEvent(article: any) {
    let thumbsDownObj = {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      pageInformation: "comprehensive-value"
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
    this.drugChannelDisplayList = JSON.parse(JSON.stringify(this.drugChannelDisplayList.map((x: any) => {
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

}
