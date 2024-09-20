import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-manage-client',
  templateUrl: './manage-client.component.html',
  styleUrls: ['./manage-client.component.scss']
})
export class ManageClientComponent {

  public searchClientText: string = "";
  public userClientList: any[] = [];
  public isSorted: boolean = true;
  public manageUserClientList: any[] = [];
  public showPagination: boolean = false;
  public showLoading: boolean = false;

  //pagination
  public recordsPerPage: number = 10;
  public currentPage: number = 1;
  pageNumbersList: number[] = [];
  public totalPages: any
  public filteredInputRecords: any[] = [];
  //pagination

  public graph_details: any = {};
  metaData: any = {};
  public email_notify: boolean = false;

  constructor(private changeDetector: ChangeDetectorRef,
    public apiService: ApiService, public commonService: CommonService) { }

  ngOnInit() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.metaData = this.commonService.getStorageItems('metaData');
    this.getUserClientList();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }

  getUserClientList() {
    this.showLoading = true;
    this.apiService.fetchnonAdminClientListData({
      "user_email": this.graph_details['mail'],
      "department": this.metaData['department_name'],
      "client_specific": true
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.email_notify = cbs['data']['email_notify'];
          cbs['data']['user_client_list'] = [...new Map(cbs['data']['user_client_list'].map((item: any) => [item['client_name'], item])).values()]
          const response = cbs['data']['user_client_list'];
          this.userClientList = response
            .map((x: any, i: number) => {
              return ({
                sNo: i + 1,
                "clientName": x['client_name'],
                "synonims": x['synonyms'],
                "isFavorite": JSON.parse(x['isFavourite'])
              })
            })
            .sort((a: any, b: any) => a.clientName.localeCompare(b.clientName))
          this.manageUserClientList = JSON.parse(JSON.stringify(this.userClientList))
          this.isSorted = true;
          this.generatePagination();
          this.showPagination = true;
        }
        this.showLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        console.error(cbe.message)
      })
  }

  markOrDemarkFav(item: any) {
    const index = this.userClientList.findIndex(x => x['clientName'] == item['clientName']);
    this.userClientList[index]['isFavorite'] = !this.userClientList[index]['isFavorite'];
    this.manageFavorites();
  }

  isSortedCheck() {
    this.isSorted = !this.isSorted;
    if (this.isSorted) this.userClientList = this.userClientList.sort((a, b) => a.clientName.localeCompare(b.clientName))
    else this.userClientList = this.userClientList.sort((a, b) => b.clientName.localeCompare(a.clientName))
    this.generatePagination();
  }

  manageFavorites() { /**saveing favorite non admin client names */
    const reqObj =
    {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "email_id": this.graph_details['mail'],
      "favourite_client_list": this.userClientList
        .filter(x => x['isFavorite'] == true)
        .map(x => x['clientName']),
      "department_name": this.metaData['department_name'],
      email_notify: this.email_notify
    }
    this.showLoading = true;
    this.apiService.saveUnsaveNonAdminFavClients(reqObj)
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) {
          this.manageUserClientList = JSON.parse(JSON.stringify(this.userClientList))
          this.generatePagination();
        }
        this.showLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        console.error(cbe.message)
      })
  }

  updateUserProfile(event?: any) {
    const reqObj =
    {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "email_id": this.graph_details['mail'],
      "favourite_client_list": this.manageUserClientList
        .filter(x => x['isFavorite'] == true)
        .map(x => x['clientName']),
      "department_name": this.metaData['department_name'],
      email_notify: this.email_notify
    }
    this.apiService.saveUnsaveNonAdminFavClients(reqObj)
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) { }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  //pagination

  // updateTable(event?: any) { /**update pagination,table records, sNo's on page change event, search event */
  //   if (this.searchClientText === "") {
  //     this.manageUserClientList = JSON.parse(JSON.stringify(this.userClientList))
  //       .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage))
  //     this.totalPages = Math.ceil(this.userClientList.length / this.recordsPerPage);
  //   } else {
  //     // this.currentPage = 1;
  //     this.manageUserClientList = JSON.parse(JSON.stringify(this.userClientList))
  //       .filter((item: any) => {
  //         return JSON.stringify(item).toLowerCase().includes(this.searchClientText.toLowerCase());
  //       })
  //       .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage));
  //     this.totalPages = Math.ceil(this.manageUserClientList.length / this.recordsPerPage);
  //   }
  //   this.reIndexList();
  // }

  updateTable(event?: any) { /**update pagination,table records, sNo's on page change event, search event */
    if (this.searchClientText != "") {
      if (this.filteredInputRecords.length == 0) this.currentPage = 1;
      this.filteredInputRecords = this.userClientList
        .filter(item => {
          return Object.keys(item).some(key => {
            return ((key !== 'client_uuid') && (String(item[key]).toLowerCase().includes(this.searchClientText.toLowerCase())))
          })
        })
      this.manageUserClientList = this.filteredInputRecords.slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage));
      this.totalPages = Math.ceil(this.filteredInputRecords.length / this.recordsPerPage);
    }
    else {
      this.clearInps()
      this.manageUserClientList = this.userClientList
        .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage))
      this.totalPages = Math.ceil(this.userClientList.length / this.recordsPerPage);
    }
    this.reIndexList();
  }

  clearInps() {
    // this.currentPage = this.currentPage == 1 ? this.currentPage++ : 1;
    this.filteredInputRecords = []; //clear filtered records
  }


  reIndexList(eventObj?: any) { /**re assign the  sNo to the filtered records*/
    this.manageUserClientList = this.manageUserClientList.map((item: any, index: any) => {
      item.sNo = ((this.currentPage - 1) * this.recordsPerPage) + (index + 1)
      return item
    })
  }

  generatePagination() {
    this.updateTable()
    const pagesToShow = 5
    const startPage = Math.max(1, this.currentPage - Math.floor(pagesToShow / 2));
    let endPage = startPage + pagesToShow - 1;
    if (endPage > this.totalPages) {
      endPage = this.totalPages;
    }
    this.pageNumbersList = Array.from({ length: (endPage - startPage + 1) }, (_, i) => startPage + i);
  }

  goToPage(page: number) {
    if (this.currentPage !== page) {
      this.currentPage = page;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

}
