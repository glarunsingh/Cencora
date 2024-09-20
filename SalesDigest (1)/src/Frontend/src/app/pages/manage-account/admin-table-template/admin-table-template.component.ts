import { ChangeDetectorRef, Component, EventEmitter, Input, Output } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { CommonService } from 'src/app/services/common.service';
import { ClientModalComponent } from 'src/app/shared/modal/client-modal/client-modal.component';
import { ConfirmModalComponent } from 'src/app/shared/modal/confirm-modal/confirm-modal.component';
import { KeywordModalComponent } from 'src/app/shared/modal/keyword-modal/keyword-modal.component';

@Component({
  selector: 'app-admin-table-template',
  templateUrl: './admin-table-template.component.html',
  styleUrls: ['./admin-table-template.component.scss']
})
export class AdminTableTemplateComponent {

  @Output() emitUpdatedRecords: any = new EventEmitter()
  @Input() columnkey1!: string;
  @Input() columnkey2!: string;
  @Input() headersList!: any[];
  @Input() totalInputRecords!: any[];
  @Input() department!: string;
  @Input() origin!: string;

  public searchKeyword: string = "";
  public isSorted: boolean = true;
  public showEditDeleteGroup: boolean[] = [];
  public selectedIndex: any;
  public tableRecords: any[] = [];
  public showCancel: boolean = false;
  public addDynamicBtnText: string = "";

  //pagination
  public recordsPerPage: number = 10;
  public currentPage: number = 1;
  pageNumbersList: number[] = [];
  public totalPages: any
  public filteredInputRecords: any[] = [];
  //pagination

  //modal
  public selectedRow: any = {};
  //modal

  constructor(private changeDetector: ChangeDetectorRef,
    private modalService: NgbModal, public commonService: CommonService) { }

  ngOnInit() {
    this.initialTableRecSet()
  }

  ngOnChanges() {
    this.initialTableRecSet()
  }

  initialTableRecSet() {
    this.addDynamicBtnText = this.origin == 'client' ? 'Add client' : 'Add keyword';
    this.tableRecords = JSON.parse(JSON.stringify(this.totalInputRecords));
    this.generatePagination();
  }

  ngAfterViewChecked() { this.changeDetector.detectChanges(); }

  isSortedCheck() {
    let fieldName = this.origin == 'client' ? 'clientName' : 'keyword';
    this.isSorted = !this.isSorted;
    if (this.isSorted) this.totalInputRecords = this.totalInputRecords.sort((a, b) => a[fieldName].localeCompare(b[fieldName]))
    else this.totalInputRecords = this.totalInputRecords.sort((a, b) => b[fieldName].localeCompare(a[fieldName]))
    this.generatePagination();
  }

  deleteRow(item: any) {
    const delModalRef = this.modalService.open(ConfirmModalComponent, { size: 'md', backdrop: 'static', centered: true });
    if (delModalRef) {
      let fieldName = this.origin == 'client' ? item.clientName : item.keyword;
      delModalRef.componentInstance.deleteConfirmDetails = { "type": "delete", data: { fieldName: fieldName } };
      delModalRef.closed.subscribe(resp => {
        if (resp && resp == "delete") {
          this.emitUpdatedRecords.emit({ emitObj: item, type: "delete" })
        }
      })
    }
  }

  //pagination

  updateTable(event?: any) { /**update pagination,table records, sNo's on page change event, search event */
    if (this.searchKeyword != "") {
      if (this.filteredInputRecords.length == 0) this.currentPage = 1;
      this.filteredInputRecords = this.totalInputRecords
        .filter(item => {
          return Object.keys(item).some(key => {
            return ((key !== 'client_uuid') && (String(item[key]).toLowerCase().includes(this.searchKeyword.toLowerCase())))
          })
        })
      this.tableRecords = this.filteredInputRecords.slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage));
      this.totalPages = Math.ceil(this.filteredInputRecords.length / this.recordsPerPage);
    }
    else {
      this.clearInps()
      this.tableRecords = this.totalInputRecords
        .slice((this.currentPage * this.recordsPerPage) - this.recordsPerPage, (this.currentPage * this.recordsPerPage))
      this.totalPages = Math.ceil(this.totalInputRecords.length / this.recordsPerPage);
    }
    this.reIndexList();
  }

  clearInps() {
    // this.currentPage = this.currentPage == 1 ? this.currentPage++ : 1;
    this.filteredInputRecords = []; //clear filtered records
  }

  reIndexList(eventObj?: any) { /**re assign the  sNo to the filtered records*/
    this.tableRecords = this.tableRecords.map((item: any, index: any) => {
      item.sNo = ((this.currentPage - 1) * this.recordsPerPage) + (index + 1)
      return item
    })
  }

  generatePagination() {
    this.updateTable()
    const pagesToShow = 5
    const startPage = Math.max(1, this.currentPage - Math.floor(pagesToShow / 2));
    let endPage = startPage + pagesToShow - 1;
    if (endPage > this.totalPages) {
      endPage = this.totalPages;
    }
    this.pageNumbersList = Array.from({ length: (endPage - startPage + 1) }, (_, i) => startPage + i);
  }

  goToPage(page: number) {
    if (this.currentPage !== page) {
      this.currentPage = page;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.generatePagination();
      // Emit an event or call a function to load data for the new page
    }
  }

  //pagination

  /**add form*/
  addNewHandler() {
    if (this.origin == 'client') {
      const addModalRef = this.modalService.open(ClientModalComponent, { size: 'lg', backdrop: 'static' });
      if (addModalRef) {
        addModalRef.componentInstance.adminClientDetails = { "type": "add", data: {}, origin: this.origin };
        addModalRef.closed.subscribe(resp => {
          if (resp && resp.type == "add") {
            this.emitUpdatedRecords.emit({ emitObj: resp['emitObj'], type: "add" })
          }
        })
      }
    }
    else {
      const addModalRef = this.modalService.open(KeywordModalComponent, { size: 'md', backdrop: 'static' });
      if (addModalRef) {
        addModalRef.componentInstance.adminKeywordDetails = { "type": "add", data: {}, origin: this.origin };
        addModalRef.closed.subscribe(resp => {
          if (resp && resp.type == "add") {
            this.emitUpdatedRecords.emit({ emitObj: resp['emitObj'], type: "add" })
          }
        })
      }
    }
  }
  /**add form*/

  /**edit form*/
  editRowHandler(item: any) {
    this.selectedRow = Object.assign({}, item);
    if (this.origin == 'client') {
      const editModalRef = this.modalService.open(ClientModalComponent, { size: 'lg', backdrop: 'static' });
      if (editModalRef) {
        editModalRef.componentInstance.adminClientDetails = {
          "type": "edit",
          data: {
            clientName: item.clientName,
            synonyms: item.synonyms,
          },
          origin: this.origin
        };
        editModalRef.closed.subscribe(resp => {
          if (resp && resp.type == "edit") {
            let emitObj = {
              client_uuid: this.selectedRow['client_uuid'],
              last_updated_by: this.selectedRow['lastUpdatedBy'],
              clientName: resp['emitObj']['clientName'],
              synonyms: resp['emitObj']['synonyms']
            }
            this.emitUpdatedRecords.emit({ emitObj, type: "edit" })
          }
        })
      }
    }
    else {
      const editModalRef = this.modalService.open(KeywordModalComponent, { size: 'md', backdrop: 'static' });
      if (editModalRef) {
        editModalRef.componentInstance.adminKeywordDetails = {
          "type": "edit",
          data: {
            keyword: item.keyword
          },
          origin: this.origin
        };
        editModalRef.closed.subscribe(resp => {
          if (resp && resp.type == "edit") {
            let emitObj = {
              keyword_uuid: this.selectedRow['keyword_uuid'],
              last_updated_by: this.selectedRow['lastUpdatedBy'],
              keyword: resp['emitObj']['keyword']
            }
            this.emitUpdatedRecords.emit({ emitObj, type: "edit" })
          }
        })
      }
    };
  }
  /**edit form*/

}
