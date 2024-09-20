import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-manage-keyword-admin',
  templateUrl: './manage-keyword-admin.component.html',
  styleUrls: ['./manage-keyword-admin.component.scss']
})
export class ManageKeywordAdminComponent {
  public departmentList: string[] = []
  public selectedDepartment: string = "";
  public userKeywordList: any[] = [];
  public showLoading: boolean = false;
  public isSorted = false;
  public paginatedKeywordAdminRecords: any[] = [];
  public keywordsHeaders: string[] = ['S.No', 'Keyword', 'Department name', 'Last updated by', 'Last updated on', 'Edit', 'Remove']
  public searchKeyword: string = "";
  public manageKeywordAdminList: any = [];
  public graph_details: any = {};

  constructor(private changeDetector: ChangeDetectorRef, public apiService: ApiService,
    public commonService: CommonService) { }

  ngOnInit() {
    this.graph_details = this.commonService.getStorageItems("graph_details");
    this.getDepartmenList();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }


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
    this.getManageKeywordAdminData();
  }

  getManageKeywordAdminData() {
    this.showLoading = true;
    this.apiService.fetchAdminKeywordListData({
      "user_email": this.graph_details['mail'],
      "department": this.selectedDepartment
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          const response = cbs['data'];
          this.userKeywordList = response
            .map((x: any, i: number) => {
              return ({
                sNo: i + 1,
                "keyword_uuid": x['keyword_uuid'],
                "keyword": x['keyword_name'],
                "departmentName": x['department_name'],
                "lastUpdatedOn": this.commonService.modifyNewsDate(x['last_updated_on'], "Do MMM - HH:mm a"),
                "lastUpdatedBy": x['last_updated_by'],
                "originalUpdatedOn": x['last_updated_on']
              })
            })
            .sort((a: any, b: any) => a.keyword.localeCompare(b.keyword))
          this.manageKeywordAdminList = JSON.parse(JSON.stringify(this.userKeywordList));
        }
        this.isSorted = true;
        this.showLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        console.error(cbe.message)
      })
  }

  collectUpdatedRecords(eventObj: { type: string, emitObj: any }) {
    let restObj = {
      api_url: "",
      payload: {},
      type: ""
    }
    switch (eventObj['type']) {
      case "add":
        restObj['api_url'] = "onboarding/admin_save_keywords_modification"
        restObj['payload'] = {
          values: eventObj.emitObj['items'].map((x: any) => ({
            "keyword_name": x['keyword'],
            "department_name": this.selectedDepartment,
            "last_updated_by": this.graph_details['displayName'],
            "last_updated_on": new Date().toISOString()
          }))
        }
        restObj['type'] = "add"
        break;
      case "edit":
        restObj['api_url'] = "onboarding/admin_save_keywords_modification"
        restObj['payload'] = {
          values: [{
            "keyword_uuid": eventObj.emitObj['keyword_uuid'],
            "keyword_name": eventObj.emitObj['keyword'],
            "department_name": this.selectedDepartment,
            "last_updated_by": this.graph_details['displayName'],
            "last_updated_on": new Date().toISOString()
          }]
        }
        restObj['type'] = "edit"
        break;
      case "delete":
        restObj['api_url'] = "onboarding/delete_keywords_admin"
        restObj['payload'] = {
          "keyword_uuid": eventObj.emitObj['keyword_uuid'],
          "keyword_name": eventObj.emitObj['keyword'],
          "department_name": this.selectedDepartment,
        }
        restObj['type'] = "delete"
        break;
    }
    this.manageKeywordAdminHandler(restObj);
  }

  manageKeywordAdminHandler(restObj: { api_url: string, payload: any, type: string }) {
    if (restObj['type'] == "delete") {
      this.apiService.deleteAdminKeywordRow(restObj['payload'])
        .subscribe((cbs: any) => {
          if (cbs['success'] == true) {
            this.searchKeyword = "";
            this.getManageKeywordAdminData();
          }
        }, (cbe: HttpErrorResponse) => {
          console.error(cbe.message)
        })
    } else {
      this.apiService.saveAdminKeywordListData(restObj['payload'])
        .subscribe((cbs: any) => {
          if (cbs['success'] == true) {
            this.searchKeyword = "";
            this.getManageKeywordAdminData();
          }
        }, (cbe: HttpErrorResponse) => {
          console.error(cbe.message)
        })
    }
  }

}
