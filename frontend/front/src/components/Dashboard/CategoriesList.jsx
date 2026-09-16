import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosConfig";
import { Pencil, Trash2, PlusCircle, Lock } from 'lucide-react';
import { HexColorPicker } from 'react-colorful';




const CategoriesList = () => {

    const [categories, setCategories] = useState([]);
    const [statusCreateCategory, setStatusCreateCategory] = useState('');
    const [statusUpdateCategory, setStatusUpdateCategory] = useState('');
    const [statusDeleteCategory, setStatusDeleteCategory] = useState('');

    const [errorCreateCategoryMsg, setErrorCreateCategoryMsg] = useState('');
    const [errorUpdateCategoryMsg, setErrorUpdateCategoryMsg] = useState('');
    const [errorDeleteCategoryMsg, setErrorDeleteCategoryMsg] = useState('');

    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showSystemModal, setShowSystemModal] = useState(false);
    const [showUpdateModal, setShowUpdateModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    const [eraseCategory, setEraseCategory] = useState(false);
    const [editCategory, setEditCategory] = useState('');

    const [updateColor, setUpdateColor] = useState('#4caf50');
    const [newColor, setNewColor] = useState('#4caf50');
    
    const [loading, setLoading] = useState(true);
    const [isModalClosing, setIsModalClosing] = useState(false);

    const VISIBLE_MS = 2000;
    const MODAL_CLOSE_MS = 300;


    useEffect(() => {
        // Simulate fetching categories from an API
       
        axiosInstance
        .get('/finances/categories/')
        .then(res => {
            setCategories(res.data);
        })
        .catch(console.error)
        .finally(() => {
            setLoading(false);
            // You can set a loading state here if needed
        });  
           
    }, []);

    const createCategory = (name, color) => {
        // API call to create a category
        const newCategory = { name, color };
        setLoading(true);
        axiosInstance.post('/finances/categories/create/', newCategory)
        .then(res => {
            setCategories(prev => [...prev, res.data]);
            setStatusCreateCategory('success');
            setShowCreateModal(false);
            setTimeout(() => {
                setIsModalClosing(true);
                setTimeout(() => {
                    setIsModalClosing(false);
                    setStatusCreateCategory('');
                }, MODAL_CLOSE_MS);
            }, VISIBLE_MS);
        })
        .catch((err) => {
            console.error(err);
            setShowCreateModal(false);
            setErrorCreateCategoryMsg(err.response?.data?.error || 'Failed to create category.');
            setStatusCreateCategory('error');
            setTimeout(() => {
                setStatusCreateCategory('');
                setErrorCreateCategoryMsg('');
            }, 3000);
        })
        .finally(() => setLoading(false));
    }


    const updateCategory = (name, color) => {
        
        
        if (name && color) {
            setLoading(true);
            axiosInstance.put(`/finances/categories/${editCategory.id}/`, { name: name, color: color})
            .then(res => {
                setCategories(prev => prev.map(cat => cat.id === editCategory.id ? res.data : cat));
                setStatusUpdateCategory('success');
                setShowUpdateModal(false);
                setTimeout(() => {
                    setIsModalClosing(true);
                    setTimeout(() => {
                        setIsModalClosing(false);
                        setStatusUpdateCategory('');
                    }, MODAL_CLOSE_MS);
                }, VISIBLE_MS);
            })
            .catch((err) => {
                console.error(err);
                setShowUpdateModal(false);
                setErrorUpdateCategoryMsg(err.response?.data?.error || 'Failed to update category.');
                setStatusUpdateCategory('error');
                setTimeout(() => {
                    setStatusUpdateCategory('');
                    setErrorUpdateCategoryMsg('');
                }, 3000);
            })
            .finally(() => setLoading(false));
        }
    }

    const deleteCategory = (category) => {
       
        setLoading(true);
        axiosInstance.delete(`/finances/categories/${category.id}/delete/`)
        .then(() => {
            setCategories(prev => prev.filter(cat => cat.id !== category.id));
            setStatusDeleteCategory('success');
            setShowDeleteModal(false);
            setTimeout(() => {
                setIsModalClosing(true);
                setTimeout(() => {
                    setIsModalClosing(false);
                    setStatusDeleteCategory('');
                }, MODAL_CLOSE_MS);
            }, VISIBLE_MS);
        
        })
        .catch((err) => {
            console.error(err);
            setShowDeleteModal(false);
            setErrorDeleteCategoryMsg(err.response?.data?.error || 'Failed to delete category.');
            setStatusDeleteCategory('error');
            setTimeout(() => {
                setStatusDeleteCategory('');
                setErrorDeleteCategoryMsg('');
            }, 3000);
        })
        .finally(() => setLoading(false));
        
    }

  return (
    <div className="categories-card--large">

        <div className="categories-card--large__body">


            {statusUpdateCategory === 'error' && (
            <div className="modal-overlay">
                <div className='modal-card'>
                    <div className="modal-title">Error updating category.</div>
                    <div className="modal-description">{errorUpdateCategoryMsg}</div>
                    <button className="modal-btn" onClick={() => setStatusUpdateCategory('')}>Ok</button>
                </div>
            </div>
            )}

            {statusCreateCategory === 'error' && (
            <div className="modal-overlay">
                <div className='modal-card'>
                    <div className="modal-title">Error creating category.</div>
                    <div className="modal-description">{errorCreateCategoryMsg}</div>
                    <button className="modal-btn" onClick={() => setStatusCreateCategory('')}>Ok</button>
                </div>
            </div>
            )}

            {statusCreateCategory === 'success' && (
            <div className={`modal-overlay ${isModalClosing ? 'closing' : ''}`}>
                <div className={`modal-card ${isModalClosing ? 'closing' : ''}`}>
                    <div className="modal-title">Category created successfully.</div>
                    <div className="modal-description">The category has been created.</div>
                    <button className="modal-btn" onClick={() => setStatusCreateCategory('')}>Ok</button>
                </div>
            </div>
            )}

            {statusUpdateCategory === 'success' && (
            <div className={`modal-overlay ${isModalClosing ? 'closing' : ''}`}>
                <div className={`modal-card ${isModalClosing ? 'closing' : ''}`}>
                    <div className="modal-title">Category updated successfully.</div>
                    <div className="modal-description">The category has been updated.</div>
                    <button className="modal-btn" onClick={() => setStatusUpdateCategory('')}>Ok</button> 
                </div>
            </div>
            )}

            {statusDeleteCategory === 'success' && (
            <div className={`modal-overlay ${isModalClosing ? 'closing' : ''}`}>
                <div className={`modal-card ${isModalClosing ? 'closing' : ''}`}>
                    <div className="modal-title">Category deleted successfully.</div>
                    <div className="modal-description">The category has been deleted.</div>
                    <button className="modal-btn" onClick={() => setStatusDeleteCategory('')}>Ok</button>
                </div>
            </div>
            )}

             {statusDeleteCategory === 'error' && (
            <div className="modal-overlay">
                <div className='modal-card'>
                    <div className="modal-title">Error deleting category.</div>
                    <div className="modal-description">{errorDeleteCategoryMsg}</div>
                    <button className="modal-btn" onClick={() => setStatusDeleteCategory('')}>Ok</button>
                </div>
            </div>
            )}

            {showSystemModal && (
            <div className="modal-overlay">
                <div className="modal-card">
                    <div className="modal-title">Protected Category</div>
                    <div className="modal-description">The "Other" category can't be edited or deleted — it's the fallback that holds transactions whose category was removed.</div>
                    <div className="modal-actions">
                        <button className="modal-btn modal-btn--confirm" onClick={() => setShowSystemModal(false)}>Got it</button>
                    </div>
                </div>
            </div>
            )}

            {showDeleteModal === true && (
                <div className="modal-overlay">
                    <div className="modal-card">
                        <div className="modal-title">Delete Category</div>
                        <div className="modal-description">Are you sure you want to delete the category?</div>
            
                        <div className="modal-form-actions">
                            <button type="button" className="modal-form-btn-cancel" onClick={() =>  setShowDeleteModal(false)}>
                                Cancel
                            </button>
                            <button type="button" className="modal-form-btn-submit" onClick={() => deleteCategory(eraseCategory)}>
                                Delete
                            </button>
                        </div>
            

                    </div>

                </div>
            )}

            
            {showUpdateModal === true && (
                <div className="modal-overlay">
                    <div className="modal-card">
                        <div className="modal-title">Update Category</div>
                        <div className="modal-description">Please enter the details to update the category</div>
                        <form className="modal-form" onSubmit={(e) => {
                        e.preventDefault();
                        updateCategory(e.target.categoryName.value|| editCategory.name  , updateColor);
                    }}>
                        <div className="form-group">
                            <label className="form-label">Name</label>
                            <input type="text" name="categoryName" defaultValue={editCategory?.name} />
                        </div>
                        <div className="color-picker-group">
                            <label className="form-label">Color</label>
                            <HexColorPicker color={updateColor} onChange={setUpdateColor} />
                            <div className="color-picker-row">
                                <div className="color-picker-preview" style={{ background: updateColor }} />
                                <input
                                    type="text"
                                    className="color-picker-hex-input"
                                    value={updateColor}
                                    onChange={e => setUpdateColor(e.target.value)}
                                    placeholder="#4caf50"
                                />
                            </div>
                        </div>
                        <div className="modal-form-actions">
                            <button type="button" className="modal-form-btn-cancel" onClick={() => { setShowUpdateModal(false); setUpdateColor('#4caf50'); }}>
                                Cancel
                            </button>
                            <button type="submit" className="modal-form-btn-submit">
                                Update
                            </button>
                        </div>
                    </form>

                    </div>

                </div>
            )}

            {showCreateModal && (
            <div className="modal-overlay">
                <div className="modal-card">
                    <div className="modal-title">Create Category</div>
                    <div className="modal-description">Please enter the details for the new category.</div>
                    <form className="modal-form" onSubmit={(e) => {
                        e.preventDefault();
                        createCategory(e.target.categoryName.value, newColor);
                    }}>
                        <div className="form-group">
                            <label className="form-label">Name</label>
                            <input type="text" name="categoryName" required />
                        </div>
                        <div className="color-picker-group">
                            <label className="form-label">Color</label>
                            <HexColorPicker color={newColor} onChange={setNewColor} />
                            <div className="color-picker-row">
                                <div className="color-picker-preview" style={{ background: newColor }} />
                                <input
                                    type="text"
                                    className="color-picker-hex-input"
                                    value={newColor}
                                    onChange={e => setNewColor(e.target.value)}
                                    placeholder="#4caf50"
                                />
                            </div>
                        </div>
                        <div className="modal-form-actions">
                            <button type="button" className="modal-form-btn-cancel" onClick={() => { setShowCreateModal(false); setNewColor('#4caf50'); }}>
                                Cancel
                            </button>
                            <button type="submit" className="modal-form-btn-submit">
                                Create
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            )}


            <h2 className="categories-card--large__header">Categories</h2>
            <div className="ctg-container">

                {loading ? 
                <div className="spinner" /> 
                : categories.length === 0 ? <p>No categories yet.</p> 
                : categories.map((category, index) => (
                    <div key={category.id} className="ctg-line">
                        <div className="ctg-item" 
                        style=
                        {{
                            color: category?.color ?? '#888',
                            background: (category?.color ?? '#888') + '1a',
                            border: `1px solid ${(category?.color ?? '#888')}80` 
                        }} 
                        >{category.name}
                        </div>
                        <div className="ctg-actions">
                            {category.is_locked ? (
                               <button className="ctg-button" onClick={() => setShowSystemModal(true)}><Lock size={14} /></button>
                            ) :  <>
                                    <button className="ctg-button" onClick={() => {setShowUpdateModal(true);setEditCategory(category); setUpdateColor(category.color);}}><Pencil size={14} /></button>
                                    <button className="ctg-button" onClick={() => {setShowDeleteModal(true);setEraseCategory(category);}}><Trash2 size={14} /></button>
                                </> }
                        </div>
                    </div>
                    
                    
                ))}
            </div>
            <div className="ctg-include" onClick={() => setShowCreateModal(true)}>
                <PlusCircle size={14} />
                <span >Add category</span>
            </div>

        </div>
        
     
    </div>
  );
}

export default CategoriesList;