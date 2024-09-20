import { HttpErrorResponse } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import * as moment from 'moment';

@Component({
  selector: 'app-breaking-news-bar',
  templateUrl: './breaking-news-bar.component.html',
  styleUrls: ['./breaking-news-bar.component.scss']
})
export class BreakingNewsBarComponent {

  @ViewChild('scrollableContent', { read: ElementRef }) scrollContent: ElementRef | any;

  headlines: any[] = []

  isMenuOpen: boolean = false;
  selectedIndex: number = 0;
  public isLoading: boolean = false;
  public errorMessage: string = "";

  constructor(public apiService: ApiService, public commonService: CommonService) { }

  ngOnInit() {
    this.breakingNewsHandler();
  }

  breakingNewsHandler() {
    const userMetaData = this.commonService.getStorageItems('metaData');
    this.isLoading = true;
    this.apiService.getBreakingNews({
      "start_date": moment().subtract(48, 'hours').utc().format("YYYY-MM-DD"), /**selected filter time frame date */
      "end_date": moment(new Date()).utc().format("YYYY-MM-DD"),  /**current date */
      "department": userMetaData['department_name']
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.headlines = cbs['data'].map((x: any) => {
            x['news_date'] = this.commonService.modifyNewsDate(x['news_date'], "DD MMM\'YY")
            return x;
          });
        } else {
          this.errorMessage = "No breaking news in the past 48 hours"
        }
        this.isLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.isLoading = false;
        console.error(cbe.message)
      })
  }


  scrollLeft() {
    if (this.scrollContent?.nativeElement) {
      this.scrollContent.nativeElement.scrollLeft -= 500
    }
  }

  scrollRight() {
    if (this.scrollContent?.nativeElement) {
      this.scrollContent.nativeElement.scrollLeft += 500
    }
  }

  toggleMenu(index: number) {
    this.selectedIndex = index
    this.isMenuOpen = !this.isMenuOpen
  }

  collectCloseEvent(event: any) {
    this.isMenuOpen = !this.isMenuOpen
  }

  modifyNewsDate(headLineNewsDate: string) {
    return
  }

}

