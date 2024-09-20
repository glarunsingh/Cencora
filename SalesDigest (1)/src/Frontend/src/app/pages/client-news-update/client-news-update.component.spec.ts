import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClientNewsUpdateComponent } from './client-news-update.component';

describe('ClientNewsUpdateComponent', () => {
  let component: ClientNewsUpdateComponent;
  let fixture: ComponentFixture<ClientNewsUpdateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ClientNewsUpdateComponent]
    });
    fixture = TestBed.createComponent(ClientNewsUpdateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
