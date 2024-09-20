import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { MsalService } from '@azure/msal-angular';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { menuItems } from 'src/app/constants/menuitems';
import { ApiService } from 'src/app/services/api.service';
import { CommonService } from 'src/app/services/common.service';
import { IdleService } from 'src/app/services/idle.service';
import { HelpLinkComponent } from 'src/app/shared/modal/help-link/help-link.component';

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss']
})
export class NavigationComponent {

  @Input() graph_details_obj!: any;
  public curr_route: string = "";
  public avatarInitials: string = "";
  public menuItems: any[] = menuItems

  public pageTitle: string = "";


  constructor(router: Router, public apiService: ApiService,
    public commonService: CommonService, private authService: MsalService,
    public idleService: IdleService, private modalService: NgbModal) {
    router.events.subscribe((url: any) => {
      this.curr_route = router.url;  // to print only path eg:"/login"
      this.pageTitle = this.menuItems.find(x => x['route'] == this.curr_route)['title']
    });
  }

  ngOnInit() {
    this.getInitials();
  }

  getInitials() {
    let input = this.graph_details_obj;
    // Trim the name and split into words, handling punctuation
    const words = input.displayName.trim().split(/\s+/);
    // If there are no words, return an empty string
    if (words.length === 0) return
    // Extract the first letter of the first two words
    const initials = words.slice(0, 2).map((word: string) => word[0].toUpperCase());
    // Join the initials into a single string
    this.avatarInitials = initials.join('');
  }

  logOut() {
    const account = this.authService.instance.getActiveAccount();
    this.authService.logoutRedirect({ account: account });
    this.idleService.stopWatching();
  }


  openHelpModal() {
    const helpModalRef = this.modalService.open(HelpLinkComponent, { size: 'md', backdrop: 'static' });
    if (helpModalRef) {
      console.info("opened")
    }
  }

}
