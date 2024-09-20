import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-results-count-widget',
  templateUrl: './results-count-widget.component.html',
  styleUrls: ['./results-count-widget.component.scss']
})
export class ResultsCountWidgetComponent {

  @Input() displayItemsList: any;
  @Output() emitFilteredItems = new EventEmitter();
  @Output() emitSelectedCount = new EventEmitter();

  public selectedPerPage: any = "All";
  public currentPage = 1;
  public resultInfo: string = '';
  public perPageOptions: any[] = []

  constructor() { }

  ngOnInit() {
    this.displayRecords();
  }

  ngOnChanges() {
    this.displayRecords();
  }

  updateRecordsPerPage(event: any) {
    // this.selectedPerPage = event['target']['value'] == "All" ? this.displayItemsList.length : +Number(event['target']['value']);
    this.selectedPerPage = event == "All" ? this.displayItemsList.length : +Number(event);
    this.currentPage = 1;
    this.displayRecords();
  }

  displayRecords() {
    this.perPageOptions = [];
    const newsListCopy = JSON.parse(JSON.stringify(this.displayItemsList))
    for (let i = 0; i < Math.ceil(newsListCopy.length / 5); i++) {
      if (this.perPageOptions.length > 4) {
        this.perPageOptions.push('All')
        break;
      }
      else {
        this.perPageOptions.push(5 * (i + 1))
      }
    }
    const selectedPage = this.selectedPerPage == "All" ? this.displayItemsList.length : +Number(this.selectedPerPage);

    const startIndex = (this.currentPage - 1) * selectedPage;
    const endIndex = Math.min(startIndex + selectedPage - 1, this.displayItemsList.length - 1);
    const filteredByItemsList = [];
    for (let i = startIndex; i <= endIndex; i++) {
      filteredByItemsList.push(newsListCopy[i])
    }
    this.resultInfo = `Showing ${startIndex + 1} - ${endIndex + 1} of ${newsListCopy.length} results`;
    this.emitFilteredItems.emit({ resultInfoText: this.resultInfo, filteredByItemsList: filteredByItemsList })
    this.emitSelectedCount.emit(this.selectedPerPage)
  }

}
