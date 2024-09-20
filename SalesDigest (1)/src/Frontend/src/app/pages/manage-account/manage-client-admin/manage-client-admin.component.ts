import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-manage-client-admin',
  templateUrl: './manage-client-admin.component.html',
  styleUrls: ['./manage-client-admin.component.scss']
})
export class ManageClientAdminComponent {
  public departmentList: string[] = []
  public selectedDepartment: string = "";
  public userClientList: any[] = [];
  public showLoading: boolean = false;
  public isSorted = false;
  public paginatedClientAdminRecords: any[] = [];
  public clientHeaders: string[] = ['S.No', 'Client Name', 'Synonyms', 'Department name', 'Last updated by', 'Last updated on', 'Edit', 'Remove']
  public searchKeyword: string = "";
  public manageClientAdminList: any = [];
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
    this.getManageCLientAdminData();
  }

  getManageCLientAdminData() {
    this.showLoading = true;
    this.apiService.fetchAdminClientListData({
      "user_email": this.graph_details['mail'],
      "department": this.selectedDepartment
    })
      .subscribe((cbs: any) => {
        if (cbs['status'] == "success") {
          const response = cbs['data'];
          this.userClientList = response
            .map((x: any, i: number) => {
              return ({
                sNo: i + 1,
                "client_uuid": x['client_uuid'],
                "clientName": x['client_name'],
                "departmentName": x['department_name'],
                "synonyms": x['synonyms'],
                "lastUpdatedOn": this.commonService.modifyNewsDate(x['last_updated_on'], "Do MMM - HH:mm a"),
                "lastUpdatedBy": x['last_updated_by'],
                "originalUpdatedOn": x['last_updated_on']
              })
            })
            .sort((a: any, b: any) => a.clientName.localeCompare(b.clientName))
          this.manageClientAdminList = JSON.parse(JSON.stringify(this.userClientList));
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
        restObj['api_url'] = "onboarding/admin_save_client_modification"
        restObj['payload'] = {
          values: eventObj.emitObj['items'].map((x: any) => ({
            "client_name": x['clientName'],
            "synonyms": x['synonyms'],
            "department_name": this.selectedDepartment,
            "last_updated_by": this.graph_details['displayName'],
            "last_updated_on": new Date().toISOString()
          }))
        }
        restObj['type'] = "add"
        break;
      case "edit":
        restObj['api_url'] = "onboarding/admin_save_client_modification"
        restObj['payload'] = {
          values: [{
            "client_uuid": eventObj.emitObj['client_uuid'],
            "client_name": eventObj.emitObj['clientName'],
            "synonyms": eventObj.emitObj['synonyms'],
            "department_name": this.selectedDepartment,
            "last_updated_by": this.graph_details['displayName'],
            "last_updated_on": new Date().toISOString()
          }]
        }
        restObj['type'] = "edit"
        break;
      case "delete":
        restObj['api_url'] = "onboarding/delete_client_admin"
        restObj['payload'] = {
          "client_uuid": eventObj.emitObj['client_uuid'],
          "client_name": eventObj.emitObj['clientName'],
          "department_name": this.selectedDepartment,
        }
        restObj['type'] = "delete"
        break;
    }
    this.manageClientAdminHandler(restObj);
  }

  manageClientAdminHandler(restObj: { api_url: string, payload: any, type: string }) {
    if (restObj['type'] == "delete") {
      this.apiService.deleteAdminClientRow(restObj['payload'])
        .subscribe((cbs: any) => {
          if (cbs['success'] == true) {
            this.searchKeyword = "";
            this.getManageCLientAdminData();
          }
        }, (cbe: HttpErrorResponse) => {
          console.error(cbe.message)
        })
    } else {
      this.apiService.saveAdminClientListData(restObj['payload'])
        .subscribe((cbs: any) => {
          if (cbs['success'] == true) {
            this.searchKeyword = "";
            this.getManageCLientAdminData();
          }
        }, (cbe: HttpErrorResponse) => {
          console.error(cbe.message)
        })
    }
  }

}
