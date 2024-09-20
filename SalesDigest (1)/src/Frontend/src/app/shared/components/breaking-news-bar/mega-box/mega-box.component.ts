import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-mega-box',
  templateUrl: './mega-box.component.html',
  styleUrls: ['./mega-box.component.scss']
})
export class MegaBoxComponent {

  @Output() emitCloseEvent = new EventEmitter();
  @Input() currentIndex: any
  @Input() newsList: any
  public currentNews: any

  constructor(public commonService: CommonService) { }

  ngOnInit() {
    this.updateContent();
  }

  showNextItem() {
    this.currentIndex = (this.currentIndex + 1) % this.newsList.length;
    this.updateContent();
  }

  showPrevItem() {
    this.currentIndex = (this.currentIndex - 1 + this.newsList.length) % this.newsList.length;
    this.updateContent();
  }

  updateContent() {
    let tempObj = this.newsList[this.currentIndex];
    this.currentNews = Object.assign({}, {
      'header': tempObj['news_title'],
      'summary': tempObj['news_summary'],
      'news_url': tempObj['news_url'],
      'client_name':tempObj['client_name']
    })
  }

  closeMegaBox() {
    this.emitCloseEvent.emit(true)
  }

}
