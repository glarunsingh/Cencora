import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SharedModule } from 'src/app/shared/shared.module';
import { AdminTableTemplateComponent } from './admin-table-template/admin-table-template.component';
import { ManageAccountComponent } from './manage-account.component';
import { ManageClientAdminComponent } from './manage-client-admin/manage-client-admin.component';
import { ManageClientComponent } from './manage-client/manage-client.component';
import { ManageKeywordAdminComponent } from './manage-keyword-admin/manage-keyword-admin.component';
import { PaginationComponent } from './pagination/pagination.component';
import { PersonalizeComponent } from './personalize/personalize.component';

export const routes =
  [
    {
      path: '', component: ManageAccountComponent
    }
  ]

@NgModule({
  declarations: [
    ManageAccountComponent,
    ManageClientComponent,
    PaginationComponent,
    AdminTableTemplateComponent,
    ManageClientAdminComponent,
    ManageKeywordAdminComponent,
    PersonalizeComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild(routes)
  ]
})
export class ManageAccountModule { }
