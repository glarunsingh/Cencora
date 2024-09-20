import { Component } from '@angular/core';

@Component({
  selector: 'app-breaking-news',
  templateUrl: './breaking-news.component.html',
  styleUrls: ['./breaking-news.component.scss']
})
export class BreakingNewsComponent {

  isAnimationPaused = false;
  isMenuOpen: boolean = false;

  headlines: any[] = [
    {
      headlineText: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ',
      headlineDate: "06th Jul'24",
      summary: "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and web page editors now use Lorem Ipsum as their default model text, and a search for 'lorem ipsum' will uncover many web sites still in their infancy. Various versions have evolved over the years, sometimes by accident, sometimes on purpose (injected humour and the like)."
    },
    {
      headlineText: 'Fusce volutpat, ante eu bibendum tincidunt',
      headlineDate: "09th Jul'24",
      summary: "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and"
    },
    {
      headlineText: 'sem lacus vehicula augue, ut suscipit.',
      headlineDate: "13th Jul'24",
      summary: "The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and web page editors now use Lorem Ipsum as their default model text, and a search for 'lorem ipsum' will uncover many web sites still in their infancy. Various versions have evolved over the years, sometimes by accident, sometimes on purpose (injected humour and the like)."
    }
  ]

  public currentIndex = 0;
  public currentNews: any = {};

  constructor() { }

  ngOnInit() {
    this.updateContent();
  }

  pauseAnimation() {
    this.isAnimationPaused = true;
  }

  resumeAnimation() {
    this.isAnimationPaused = false;
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen
    this.isAnimationPaused = true;
  }

  showNextItem() {
    this.currentIndex = (this.currentIndex + 1) % this.headlines.length;
    this.updateContent();
  }

  showPrevItem() {
    this.currentIndex = (this.currentIndex - 1 + this.headlines.length) % this.headlines.length;
    this.updateContent();
  }

  updateContent() {
    let tempObj = this.headlines[this.currentIndex];
    this.currentNews = Object.assign({}, {
      'header': tempObj['headlineText'],
      'summary': tempObj['summary']
    })

  }

}
