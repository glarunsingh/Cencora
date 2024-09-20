import { Component } from '@angular/core';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-manage-account',
  templateUrl: './manage-account.component.html',
  styleUrls: ['./manage-account.component.scss']
})
export class ManageAccountComponent {

  public manageTopics: string[] = []
  public activeIndex: number = 0;
  public isAdmin: boolean = false;
  public userMetaData: any = {}

  constructor(public commonService: CommonService) { }

  ngOnInit() {
    this.userMetaData = this.commonService.getStorageItems('metaData');
    if (this.userMetaData.role == 'Admin') this.manageTopics = ['Manage clients', 'Manage keywords', 'Personalize'];
    else this.manageTopics = ['Manage clients']
  }
}