import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {

  cardsData = [
    {
      "title": "Client digest",
      "icon": "onboarding-people",
      "department": "Health systems",
      "lastAccessed": "5",
      "accessGrantedStatus": "Access granted",
      "route": "/client-news-update"
    },
    {
      "title": "Keyword digest",
      "icon": "onboarding-keyword-digest",
      "department": "Health systems",
      "lastAccessed": "10",
      "accessGrantedStatus": "Access granted",
      "route": "/keyword-digest"
    },
    {
      "title": "Comprehensive market value",
      "icon": "Globe",
      "department": "Health systems",
      "lastAccessed": "12",
      "accessGrantedStatus": "Access granted",
      "route": "/comprehensive-market-view"
    }
  ]

  homeInfoData: any[] = [
    {
      "title": "Access application",
      "subField": "Log in effortlessly to our intuitive platform",
      "icon": "touch-id-1",
      "style": {
        "marginBottom": "mb-3"
      }
    },
    {
      "title": "Ask domain specific questions/prompts",
      "subField": "Tailor research to your domain with ease",
      "icon": "ask-domain",
      "style": {
        "marginBottom": "mb-3"
      }
    },
    {
      "title": "Consume response",
      "subField": "Get insightful, relevant responses instantly",
      "icon": "task-list-pen",
      "style": {
        "marginBottom": "mb-0"
      }
    }
  ]

  public metaData: any = {};

  constructor(private router: Router, public commonService: CommonService) { }

  ngOnInit() {
    this.metaData = this.commonService.getStorageItems('metaData');
  }

  goToPage(route: string) {
    this.router.navigate([route])
  }

}
