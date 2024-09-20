import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-comprehensive-market-value',
  templateUrl: './comprehensive-market-value.component.html',
  styleUrls: ['./comprehensive-market-value.component.scss']
})
export class ComprehensiveMarketValueComponent {

  subTopics: string[] = [];
  activeIndex = 0;
  public lastSixMonthsList: any[] = [];
  public appliedSourcesList: any[] = [];
  public selectedTimeFrame: string = "Past 3 weeks";
  public showLoading: boolean = false;
  public sourceList: any[] = []
  public clientNamesList: any[] = []
  public definitiveTableList: any[] = []
  public sentimentList: any[] = [];
  public timeStampsList: any[] = [
    'Past 1 week',
    'Past 3 weeks',
    'Past 5 weeks',
    'Past 180 days'
  ]
  public appliedTablesList: any[] = [];
  public selectedClientName: string = "";
  public sourceNamesFilterCountObj: any = { 'name': "Source", total: 0 };
  public definitiveTableFilterObj: any = { 'name': "Table", total: 0 };
  sentimentFilterCountObj: any = { 'name': "Sentiment", total: 0 }

  public graph_details: any = {};
  public metaData: any = {};

  constructor(public commonService: CommonService,
    private changeDetector: ChangeDetectorRef,
    public apiService: ApiService) { }

  ngOnInit() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.metaData = this.commonService.getStorageItems('metaData');
    if (this.metaData['department_name'] == "Government sales") {
      this.subTopics = ['Other news'];
      this.activeIndex = 1;
    } else {
      this.subTopics = ['Definitive Healthcare', 'Other news'];
      this.activeIndex = 0;
    }

    this.getDefinitiveClientNames();
    this.getOtherNewsFiltersData();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }

  getOtherNewsFiltersData() {

    this.apiService.getClientNewsClientList({
      "user_email": this.graph_details['mail'],
      "department": this.metaData['department_name'],
      "client_specific": false
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          cbs['data']['sourceList'] = [...new Map(cbs['data']['sourceList'].map((item: any) => [item['name'], item])).values()]
          if (cbs['data']['sourceList'].length) {
            this.manageSourceFilters(cbs);
            this.manageSentimentsFilters({ data: { sentiment: [{ 'name': 'Positive' }, { 'name': 'Negative' }, { 'name': 'Neutral' }] } });
          }
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }


  manageSourceFilters(response: any) {
    this.sourceList = [];
    // Process sourceList
    const sourceList = this.transformList(response.data.sourceList, 'name');
    sourceList.map(x => x['isChecked'] = true) /**if no fav is available then make all as checked */
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
    this.sentimentList = sentimentFilters;
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

  toggleCheckbox(item: { from: string, data: any[] }) {
    this.appliedSourcesList = this.commonService.createFilterItemsList(item).filter(x => x['from'] != 'Table');
    this.sourceNamesFilterCountObj['total'] = this.appliedSourcesList.filter(x => x['from'] == "Source").length;
    this.sentimentFilterCountObj['total'] = this.appliedSourcesList.filter(x => x['from'] == "Sentiment").length;
  }

  collectRadioButtonChange(args: string) {
    this.selectedTimeFrame = args;
  }

  toggleTableCheckbox(item: { from: string, data: any[] }) {
    this.appliedTablesList = this.commonService.createFilterItemsList(item);
    this.definitiveTableFilterObj['total'] = this.appliedTablesList.filter(x => x['from'] == "Table").length;
  }

  collectClientButtonChange(args: string) {
    this.selectedClientName = args;
  }

  collectSourceClearAll(event: string) { /**clear all the applied filters on box cross icon click */
    if (event == "Source") {
      this.sourceList.map(x => x['isChecked'] = false)
      this.sourceNamesFilterCountObj['total'] = 0;
      this.appliedSourcesList.map(x => {
        if (x['from'] == "Source") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Source')
    }
    if (event == "Sentiment") {
      this.sentimentList.map(x => x['isChecked'] = false)
      this.sentimentFilterCountObj['total'] = 0;
      this.appliedSourcesList.map(x => {
        if (x['from'] == "Sentiment") x['isChecked'] = false;
      })
      this.commonService.updateMapByKey('Sentiment')
    }
  }

  clearAllTableFilters(event: string) {
    this.definitiveTableList.map(x => x['isChecked'] = false);
    this.appliedTablesList.map(x => x['isChecked'] = false);
    this.definitiveTableFilterObj['total'] = 0;
    this.appliedSourcesList.map(x => {
      if (x['from'] == "Table") x['isChecked'] = false;
    })
    this.commonService.updateMapByKey('Table')
  }

  getDefinitiveClientNames() {
    const metaData = this.commonService.getStorageItems('metaData');
    this.apiService.getDeinitiveClienList({
      "department": metaData['department_name'],
      "source": "Definitive"
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          if (cbs['data']['client'].length) {
            this.clientNamesList = [...new Set(cbs['data']['client'])];
            if (this.clientNamesList.length) this.selectedClientName = this.clientNamesList[0];
            // this.definitiveTableList[1]['isChecked'] = true;
            // this.toggleTableCheckbox({ from: 'Table', data: this.definitiveTableList.filter((item: any) => item.isChecked) })
            const definitiveTableList = [
              { isChecked: false, text: 'Financial Strength' },
              { isChecked: false, text: 'Network Strength' },
              { isChecked: false, text: 'Clinical' },
              { isChecked: false, text: 'Company Details' },
              { isChecked: false, text: 'Executives' },
              { isChecked: false, text: 'Financial' },
              { isChecked: false, text: 'Quality' },
              { isChecked: false, text: 'Technology & Innovation' }
            ]
            this.definitiveTableList = definitiveTableList;
            this.definitiveTableList.map(x => x['isChecked'] = true);
            this.definitiveTableList.unshift({ isChecked: false, text: 'All' });

            // Call toggleTableCheckbox function with selected tables
            this.toggleTableCheckbox({ from: 'Table', data: this.definitiveTableList });
            this.definitiveTableList = this.commonService.manageAllCheckOption(JSON.parse(JSON.stringify(this.definitiveTableList)))
          }
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  changeTab(index: number) {
    this.activeIndex = this.subTopics.length == 1 ? this.activeIndex : index;
  }

  ngOnDestroy() {
    this.commonService.clearFilters();
  }

}

