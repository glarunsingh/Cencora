import { ChangeDetectorRef, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-news-tile',
  templateUrl: './news-tile.component.html',
  styleUrls: ['./news-tile.component.scss']
})
export class NewsTileComponent {

  @Input() newsTileData!: any;
  @Input() maxLength!: number;
  @Input() displayTitle!:string
  @Input() displayKey!:string
  @Output() emitThumbsUpEvent = new EventEmitter();
  @Output() emitThumbsDownEvent = new EventEmitter();
  public article: any = {};

  constructor(public commonService: CommonService,private changeDetector: ChangeDetectorRef) { }

  ngOnInit() {
    this.article = JSON.parse(JSON.stringify(this.newsTileData))
  }

  ngOnChanges() {
    this.article = JSON.parse(JSON.stringify(this.newsTileData))
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }

  showMore() {
    this.article['isActive'] = true;
  }

  showLess() {
    this.article['isActive'] = false;
  }

  thumbsUpHandler(article: any) {
    const thumbsUpObj = {
      news_url: article.news_url,
      feedback: 'isThumbsUp',
      value: !article['isThumbsUp'],
      category: "",
      comment: "",
      isThumbsUp:article['isThumbsUp'],
      isThumbsDown:article['isThumbsDown']
    }
    this.emitThumbsUpEvent.emit(thumbsUpObj)
  }

  thumbsDownHandler(article: any) {
    const thumbsDownObj = {
      news_url: article.news_url,
      feedback: 'isThumbsDown',
      value: !article['isThumbsDown'],
      category: "",
      comment: "",
      isThumbsUp:article['isThumbsUp'],
      isThumbsDown:article['isThumbsDown']
    }
    this.emitThumbsDownEvent.emit(thumbsDownObj)
  }

}
