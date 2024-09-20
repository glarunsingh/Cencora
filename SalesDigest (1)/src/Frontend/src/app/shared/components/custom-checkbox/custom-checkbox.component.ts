import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-custom-checkbox',
  templateUrl: './custom-checkbox.component.html',
  styleUrls: ['./custom-checkbox.component.scss']
})
export class CustomCheckboxComponent {

  @Input() checkboxItemsList: any[] | undefined;
  @Input() updatedList: any
  @Input() title: string | undefined
  @Input() instanceId: string | undefined
  @Input() isFilterEnabled: boolean | undefined

  @Output() emitCheckboxChnage = new EventEmitter()

  public searchItem: string = ""
  public isEmpty: boolean = false;
  public showLoading: boolean = false;

  constructor(public commonService: CommonService) { }

  ngOnInit() {
    this.loadItems();
  }

  ngOnChanges() {
    this.loadItems();
  }

  loadItems() {
    this.showLoading = true;
    if (this.checkboxItemsList?.length) {
      this.isEmpty = false;
      this.showLoading = false;
    } else {
      this.isEmpty = true;
      this.showLoading = false;
    }
  }

  emitChange(event?: any) {
    if (event?.['text'] == 'All') {
      this.checkboxItemsList?.map(x => {
        x['isChecked'] = event['isChecked']
        return x
      })
    }
    else if (event?.['text'] != 'All' && this.checkboxItemsList?.some(x => x['text'] == "All")) {
      this.checkboxItemsList = this.commonService.manageAllCheckOption(this.checkboxItemsList);
    }
    else {
      if (event?.['isChecked'] == false) {
        this.checkboxItemsList?.map(x => {
          if (x['text'] == "All") x['isChecked'] = false
          return x;
        })
      }
    }

    let obj = { from: this.title, data: this.checkboxItemsList?.filter(x => x['isChecked'] == true && x['text'] != 'All') }
    this.emitCheckboxChnage.emit(obj)
  }

  resetFilters() {
    this.checkboxItemsList?.map(x => x['isChecked'] = false);
    this.searchItem = "";
    this.emitChange();
  }

}
