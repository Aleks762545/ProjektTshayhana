// frontend/admin/js/orders.js
import { AdminAPI, toast } from '/admin/js/admin-common.js';

let orders = [];

const waitingList = document.getElementById('waitingList');
const orderDetail = document.getElementById('orderDetail');

async function fetchOrders(){
  waitingList.innerHTML = '<div class="hint">Загрузка...</div>';
  try{
    const res = await AdminAPI.fetchJSON('/api/orders');
    orders = Array.isArray(res) ? res : [];
    // нормализуем статус
    orders.forEach(o => { if(!o.status) o.status = 'pending'; });
    renderOrders();
  }catch(e){
    waitingList.innerHTML = '<div class="hint">Ошибка загрузки</div>';
    console.error(e);
    toast('Ошибка загрузки заказов: '+e.message);
  }
}

function renderOrders(){
  waitingList.innerHTML = '';
  if(orders.length === 0){
    waitingList.innerHTML = '<div class="hint">Нет заказов</div>';
    return;
  }

  const orderRank = {pending:1,in_progress:2,ready:3,delivered:4,complete:5};
  const sorted = [...orders].sort((a,b)=>orderRank[a.status]-orderRank[b.status]);

  for(const o of sorted){
    const c = document.createElement('div'); c.className='order-card';
    c.innerHTML = `<div class="meta"><div>#${o.id}</div><div>${o.created_at ?? ''}</div></div>
      <div>Стол: ${o.table_number ?? '-'}</div>
      <div class="items">${(o.items||[]).map(it=>`<div>${it.dish_id} × ${it.quantity}</div>`).join('')}</div>
      <div>Статус: ${o.status}</div>`;

    const btn = document.createElement('button');
    btn.className = 'small-btn';

    if(o.status === 'pending'){
      btn.textContent = 'Принять';
      btn.onclick = ()=>changeStatus(o,'in_progress');
    } else if(o.status === 'in_progress'){
      btn.textContent = 'Готов';
      btn.onclick = ()=>changeStatus(o,'ready');
    } else if(o.status === 'ready'){
      btn.textContent = 'Выдать';
      btn.onclick = ()=>changeStatus(o,'delivered');
    } else if(o.status === 'delivered' || o.status === 'complete'){
      btn.textContent = 'Удалить';
      btn.onclick = ()=>deleteOrder(o);
    }

    c.appendChild(btn);
    c.onclick = ()=>showDetail(o);
    waitingList.appendChild(c);
  }
}

function showDetail(o){
  orderDetail.innerHTML = '';
  const d = document.createElement('div'); d.className='order-card';
  d.innerHTML = `<div class="meta"><div>Заказ #${o.id}</div><div>${o.created_at ?? ''}</div></div>
    <div>Гость: ${o.guest_name ?? o.guest_phone ?? '-'}</div>
    <div class="items">${(o.items||[]).map(it=>`<div>${it.dish_id} × ${it.quantity}</div>`).join('')}</div>
    <div>Статус: ${o.status}</div>`;
  orderDetail.appendChild(d);
}

function changeStatus(order, status){
  order.status = status;
  toast(`Заказ #${order.id} → ${status}`);
  renderOrders();
}

function deleteOrder(order){
  orders = orders.filter(o => o.id !== order.id);
  toast(`Заказ #${order.id} удалён`);
  renderOrders();
}

// автообновление
document.addEventListener('DOMContentLoaded', () => {
  fetchOrders();
  setInterval(fetchOrders, 10000);
});

export { fetchOrders, changeStatus, deleteOrder };
