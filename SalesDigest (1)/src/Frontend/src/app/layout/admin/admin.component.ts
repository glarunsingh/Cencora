import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { IdleService } from 'src/app/services/idle.service';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent {

  public current_route: string = "";
  public graph_details_obj: any = {};

  constructor(router: Router, public apiService: ApiService,
    public commonService: CommonService, public idleService: IdleService) {
    router.events.subscribe((url: any) => {
      this.current_route = router.url;
    });
  }

  getTopCssByRoute() {
    if (this.current_route == '/onboarding') return 'onboarding-top';
    if (this.current_route == '/manage-account') return 'manage-top'
    return 'regular-top'
  }

  ngOnInit() {
    this.idleService.startWatching();
  }

  enableLayout() {
    const graph_details = this.commonService.getStorageItems("graph_details");
    if (graph_details && Object.keys(graph_details).length) {
      this.graph_details_obj = graph_details;
      return true;
    }
    return false;
  }

  ngOnDestroy() {
    localStorage.clear();
  }

}
