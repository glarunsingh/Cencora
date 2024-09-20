import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-personalize',
  templateUrl: './personalize.component.html',
  styleUrls: ['./personalize.component.scss']
})
export class PersonalizeComponent {

  public departmentList: string[] = []
  public selectedDepartment: string = "";
  public showPagination: boolean = false;
  public showLoading: boolean = false;
  public isSorted = false;
  public adminClientList: any[] = [];
  public adminClientList_clone: any[] = [];

  //pagination
  public recordsPerPage: number = 10;
  public currentPage: number = 1;
  pageNumbersList: number[] = [];
  public totalPages: any;
  public filteredInputRecords: any[] = [];
  //pagination

  public graph_details: any = {};
  userMetaData: any = {};
  public searchClientText: string = "";
  public showSearchSort: boolean = false;

  public email_notify: boolean = false;

  constructor(private changeDetector: ChangeDetectorRef,
    public apiService: ApiService, public commonService: CommonService) { }

  ngOnInit() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.userMetaData = this.commonService.getStorageItems('metaData');
    this.getDepartmenList();
  }

  getDepartmenList() {
    this.apiService.getDepartmentList()
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) {
          this.departmentList = cbs['data']
        }
      }, (cbe: HttpErrorResponse) => {
        console.error(cbe.message)
      })
  }

  setDepartment(event: string) {
    this.selectedDepartment = event;
    if (this.userMetaData['department_name'] == this.selectedDepartment) {
      this.manageFavorites((callBackSuccess: string) => {
        if (callBackSuccess == "next") this.getAdminClientsList();
      }, 'sameDepartment');
    } else {
      this.manageFavorites((callBackSuccess: string) => {
        if (callBackSuccess == "next") this.getAdminClientsList();
      }, 'differentDepartment');
    }
    this.userMetaData['department_name'] = this.selectedDepartment;
    this.commonService.setStorageItems("metaData", JSON.stringify(this.userMetaData))
  }

  getAdminClientsList() {
    this.showLoading = true;
    this.apiService.fetchnonAdminClientListData({
      "user_email": this.graph_details['mail'],
      "department": this.selectedDepartment,
      "client_specific": true
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          this.email_notify = cbs['data']['email_notify'];
          cbs['data']['user_client_list'] = [...new Map(cbs['data']['user_client_list'].map((item: any) => [item['client_name'], item])).values()]
          const response = cbs['data']['user_client_list'];
          this.adminClientList = response
            .map((x: any, i: number) => {
              return ({
                sNo: i + 1,
                "clientName": x['client_name'],
                "synonyms": x['synonyms'],
                "isFavorite": JSON.parse(x['isFavourite'])
              })
            })
            .sort((a: any, b: any) => a.clientName.localeCompare(b.clientName))
          this.adminClientList_clone = JSON.parse(JSON.stringify(this.adminClientList));
          this.showLoading = false;
          this.isSorted = true;
          this.generatePagination();
          this.showPagination = true;
          this.showSearchSort = true;
        }
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        this.showSearchSort = false;
        console.error(cbe.message)
      });
  }

  markOrDemarkFav(item: any) {
    const index = this.adminClientList.findIndex(x => x['clientName'] == item['clientName']);
    this.adminClientList[index]['isFavorite'] = !this.adminClientList[index]['isFavorite'];
    this.updateUserProfile();
  }

  isSortedCheck() {
    this.isSorted = !this.isSorted;
    if (this.isSorted) this.adminClientList = this.adminClientList.sort((a, b) => a.clientName.localeCompare(b.clientName))
    else this.adminClientList = this.adminClientList.sort((a, b) => b.clientName.localeCompare(a.clientName))
    this.generatePagination();
  }

  manageFavorites(callBackSuccess: any, type: string) { /**saveing favorite non admin client names */
    const reqObj =
    {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "email_id": this.graph_details['mail'],
      "favourite_client_list": this.adminClientList_clone
        .filter(x => x['isFavorite'] == true)
        .map(x => x['clientName']),
      "department_name": this.selectedDepartment,
      email_notify: this.email_notify,
      department_change: type == "sameDepartment" ? false : true
    }
    this.showLoading = true;
    this.apiService.saveUnsaveNonAdminFavClients(reqObj)
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) {
          callBackSuccess("next")
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
      "favourite_client_list": this.adminClientList_clone
        .filter(x => x['isFavorite'] == true)
        .map(x => x['clientName']),
      "department_name": this.selectedDepartment,
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
  //     this.adminClientList_clone = JSON.parse(JSON.stringify(this.adminClientList))
  //       .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage))
  //     this.totalPages = Math.ceil(this.adminClientList.length / this.recordsPerPage);
  //   } else {
  //     // this.currentPage = 1;
  //     this.adminClientList_clone = JSON.parse(JSON.stringify(this.adminClientList))
  //       .filter((item: any) => {
  //         return JSON.stringify(item).toLowerCase().includes(this.searchClientText.toLowerCase());
  //       })
  //       .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage));
  //     this.totalPages = Math.ceil(this.adminClientList_clone.length / this.recordsPerPage);
  //   }
  //   this.reIndexList();
  // }

  updateTable(event?: any) { /**update pagination,table records, sNo's on page change event, search event */
    if (this.searchClientText != "") {
      if (this.filteredInputRecords.length == 0) this.currentPage = 1;
      this.filteredInputRecords = this.adminClientList
        .filter(item => {
          return Object.keys(item).some(key => {
            return ((key !== 'client_uuid') && (String(item[key]).toLowerCase().includes(this.searchClientText.toLowerCase())))
          })
        })
      this.adminClientList_clone = this.filteredInputRecords.slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage));
      this.totalPages = Math.ceil(this.filteredInputRecords.length / this.recordsPerPage);
    }
    else {
      this.clearInps()
      this.adminClientList_clone = this.adminClientList
        .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage))
      this.totalPages = Math.ceil(this.adminClientList.length / this.recordsPerPage);
    }
    this.reIndexList();
  }

  clearInps() {
    // this.currentPage = this.currentPage == 1 ? this.currentPage++ : 1;
    this.filteredInputRecords = []; //clear filtered records
  }

  reIndexList(eventObj?: any) { /**re assign the  sNo to the filtered records*/
    this.adminClientList_clone = this.adminClientList_clone.map((item: any, index: any) => {
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
