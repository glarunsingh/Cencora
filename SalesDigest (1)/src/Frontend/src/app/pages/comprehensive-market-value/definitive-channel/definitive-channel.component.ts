import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-definitive-channel',
  templateUrl: './definitive-channel.component.html',
  styleUrls: ['./definitive-channel.component.scss']
})
export class DefinitiveChannelComponent {

  @Output() emitClearAllTableFilters = new EventEmitter();
  @Input() selectedClientName: string | undefined;
  @Input() appliedTablesList: any[] | undefined;
  @Input() definitiveTableFilterObj: any
  public definitiveData: any = {}
  public showLoading: boolean = false;
  public selectedTables: string[] | undefined = [];
  public showTables: boolean = false;
  public loadingText: string = "";
  public showBanner: boolean = false;
  public bannerText: string = "";

  constructor(public apiService: ApiService, public commonService: CommonService) { }

  ngOnInit() {
  }

  ngOnChanges() {
    this.getDefinitiveData();
    this.updateTables();
  }

  clearAllSelectedTables(args: string) {
    this.showTables = false;
    this.emitClearAllTableFilters.emit(args);
    this.getDefinitiveData();
  }

  getDefinitiveData() {
    if (this.selectedClientName && this.appliedTablesList?.filter(x => x['isChecked']).length) {
      let reqObj =
      {
        "source_name": "Definitive",
        "client": this.selectedClientName
      }
      this.showBanner = false;
      if (reqObj.client) {
        this.showLoading = true;
        this.loadingText = 'Fetching records for the selected filter criteria';
        this.apiService.getDeinitiveChannelData(reqObj)
          .subscribe((cbs: any) => {
            if (cbs['status'] == "success") {
              let result: any = {}
              let tempDefinitiveDataObj = JSON.parse(JSON.stringify(cbs['data'][0]))
              for (let key in tempDefinitiveDataObj) {
                if (tempDefinitiveDataObj.hasOwnProperty(key)) {
                  result[key] = Object.entries(tempDefinitiveDataObj[key]).map(([key, value], i) => {
                    return ({
                      sNo: i + 1,
                      metric: key,
                      value: value
                    })
                  })
                }
              }
              this.definitiveData = Object.assign({}, result);
              this.showBanner = false;
            }
            else {
              this.showBanner = false;
              this.bannerText = cbs['message'];
            }
            this.showLoading = false;
          }, (cbe: HttpErrorResponse) => {
            this.showLoading = false;
            this.showBanner = false;
            console.error(cbe.message)
          })
      }
    }
    else {
      this.showBanner = true;
      this.bannerText = "Kindly choose at least one table from the filter."
    }
    this.commonService.scrollToTop()
  }

  isDefinitiveTablesValid() {
    return Object.keys(this.definitiveData).length ? true : false
  }

  // getHeadersAndValues(table: string) {
  //   const entries = Object.entries(this.definitiveData[table]);
  //   const headers = entries.map(([key]) => key)
  //   const values = entries.map(([, value]) => value)
  //   return { headers, values }
  // }

  updateTables() {
    this.selectedTables = this.appliedTablesList?.filter(x => x['isChecked'])?.map(x => x['text'])
    if (this.selectedTables?.length) this.showTables = true;
    this.commonService.scrollToTop()
  }

  definitiveDownloadHandler() {
    this.showLoading = true;
    this.loadingText = 'Downloading the file for' + '' + this.selectedClientName + '_' + 'Definitive_Healthcare_';
    const reqObj =
    {
      "table_list": this.selectedTables,
      "source": "Definitive",
      "client_name": this.selectedClientName
    }
    this.apiService.downloadDefinitiveData(reqObj)
      .subscribe((cbs: any) => {
        const url = window.URL.createObjectURL(cbs);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.selectedClientName + '_' + 'Definitive_Healthcare_' + '' + this.commonService.getTimeStampFormat() + '.xlsx'; // Set the desired filename
        a.click();
        window.URL.revokeObjectURL(url);
        this.showLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        console.error(cbe.message)
      })
  }

}
