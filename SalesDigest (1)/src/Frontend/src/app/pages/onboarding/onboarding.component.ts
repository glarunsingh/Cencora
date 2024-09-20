import { HttpErrorResponse } from '@angular/common/http';
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.component.html',
  styleUrls: ['./onboarding.component.scss']
})
export class OnboardingComponent {

  public departmentList: string[] = []

  public clientBoxList: any[] = []
  public isConsentChecked: boolean = false;
  public searchText: string = ""
  public selectedDepartment: string = "";
  public showLoading: boolean = false;
  public showAlert: boolean = false;

  onBoardingInfoData: any[] = [
    {
      "title": "Client digest",
      "subField": "Access customized insights on preferred clients for targeted research.",
      "icon": "onboarding-people",
      "style": {
        "marginBottom": "mb-3"
      }
    },
    {
      "title": "Keyword digest",
      "subField": "Research efficiently with focused keyword-based data analysis.",
      "icon": "onboarding-keyword-digest",
      "style": {
        "marginBottom": "mb-3"
      }
    },
    {
      "title": "Comprehensive market value",
      "subField": "Utilize social analytics to evaluate market trends and sentiment.",
      "icon": "Globe",
      "style": {
        "marginBottom": "mb-0"
      }
    }
  ]
  public userMetaData: any = {};
  public userName: string = "";
  public graph_details: any = {};

  constructor(private apiService: ApiService, private router: Router, public commonService: CommonService) { }

  ngOnInit() {
    let graph_details_obj!: any
    this.commonService.castUserGraphDetails.subscribe(graph_details => {
      if (graph_details && Object.keys(graph_details).length) {
        graph_details_obj = JSON.parse(graph_details)
      } else {
        graph_details_obj = this.commonService.getStorageItems("graph_details");
      }
      this.graph_details = graph_details_obj
      this.fetchUserDetails();
    });
  }

  fetchUserDetails() {
    this.userName = this.graph_details?.['displayName'];
    this.userMetaData = this.commonService.getStorageItems('metaData');
    if (this.userMetaData['role'] == "Admin") {
      this.getDepartmenList()
    } else {
      this.selectedDepartment = this.userMetaData['department_name'];
      this.getCLientListByDepartment();
    }
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
    this.searchText = "";
    this.getCLientListByDepartment();
  }

  getCLientListByDepartment() {
    this.showLoading = true;
    this.apiService.getClientNamesList(this.selectedDepartment)
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) {
          this.clientBoxList = [];
          this.clientBoxList = cbs['data']
            .map((x: any) => {
              return ({
                "departmentName": this.selectedDepartment,
                "clientName": x,
                "text": x,
                "isFavourite": false
              })
            })
            .sort((a: any, b: any) => a.clientName.localeCompare(b.clientName))
          this.showAlert = false;
        } else {
          this.showAlert = true;
        }
        this.showLoading = false;
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        this.showAlert = false;
      })
  }

  markOrDemarkFav(item: any) {
    const index = this.clientBoxList.findIndex(x => x['text'] == item['text']);
    this.clientBoxList[index]['isFavourite'] = !this.clientBoxList[index]['isFavourite']
  }

  submitOrSkip(args: string) {
    this.showLoading = true
    let userDetailsObj =
    {
      "emp_id": this.graph_details['id'],
      "first_name": this.graph_details['givenName'],
      "last_name": this.graph_details['surname'],
      "email_id": this.graph_details['mail'],
      "favourite_client_list": args == 'skip' ? [] : this.clientBoxList
        .filter(x => x['isFavourite'] == true)
        .map(x => x['clientName']),
      "email_notify": this.isConsentChecked == true ? true : false,
      "department_name": this.selectedDepartment
    }

    this.apiService.sendUserOnBoardinDetails(userDetailsObj)
      .subscribe((cbs: any) => {
        if (cbs['success'] == true) {
          this.showLoading = false;
          this.userMetaData['department_name'] = this.selectedDepartment;
          this.commonService.setStorageItems("metaData", JSON.stringify(this.userMetaData))
          this.router.navigate(['/home'])
        }
      }, (cbe: HttpErrorResponse) => {
        this.showLoading = false;
        console.error(cbe.message)
      })
  }

}
