import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-custom-radiobutton',
  templateUrl: './custom-radiobutton.component.html',
  styleUrls: ['./custom-radiobutton.component.scss']
})
export class CustomRadiobuttonComponent {

  @Output() emitRadioButtonChange = new EventEmitter();

  @Input() radioItemsList: any[] | undefined;
  @Input() title: string | undefined;
  @Input() instanceId: string | undefined;
  @Input() defaultItem: string | undefined;
  @Input() isFilterEnabled: boolean | undefined

  public selectedTimeFrame: string = "";
  public searchItem: string = ""

  public isEmpty: boolean = false;
  public showLoading: boolean = false;

  constructor() { }

  ngOnInit() {
    this.loadItems();
  }

  ngOnChanges() {
    this.loadItems();
  }

  loadItems() {
    this.showLoading = true;
    if (this.radioItemsList?.length) {
      this.isEmpty = false;
      this.showLoading = false;
      this.assignDefaultAndEmit()
    } else {
      this.isEmpty = true;
      this.showLoading = false;
    }
  }

  assignDefaultAndEmit() {
    if (this.defaultItem) {
      this.selectedTimeFrame = this.defaultItem;
      this.emitRadioButtonChange.emit(this.selectedTimeFrame)
    }
  }

  changeTimeFrame(event: string) {
    this.emitRadioButtonChange.emit(this.selectedTimeFrame)
  }

}
