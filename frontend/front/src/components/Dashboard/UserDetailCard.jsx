import { useState, useEffect, useRef } from "react";
import axiosInstance from "../../api/axiosConfig";
import PhoneInput from 'react-phone-input-2';
import 'react-phone-input-2/lib/style.css';
import TimezoneSelect from 'react-timezone-select';

const UserDetailCard = () => {

    const [dbData, setdbData] = useState(null);
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        profile: {
            display_name: "",
            notification_email: "",
            phone: "",
            timezone: ""
        }
    });
    const [loading, setLoading] = useState(true);
    const [phoneCountry, setPhoneCountry] = useState('br');
    const [phoneKey, setPhoneKey] = useState(0);
    const [status, setStatus] = useState('idle');
    const [errors, setErrors] = useState({});
    const phoneInputRef = useRef(null);

    const validate = () => {
        const errs = {};
        if (!formData.first_name.trim()) errs.first_name = 'First name is required.';
        if (!formData.last_name.trim()) errs.last_name = 'Last name is required.';
        if (formData.profile.notification_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.profile.notification_email))
            errs.notification_email = 'Invalid email format.';
        if (formData.profile.phone && formData.profile.phone.replace(/\D/g, '').length < 8)
            errs.phone = 'Phone number is too short.';
        return errs;
    };

    const hasChanges = () => {
        if (!dbData) return false;
        return (
            formData.first_name !== (dbData.first_name || '') ||
            formData.last_name !== (dbData.last_name || '') ||
            formData.profile.display_name !== (dbData.profile?.display_name || '') ||
            formData.profile.notification_email !== (dbData.profile?.notification_email || '') ||
            formData.profile.phone !== (dbData.profile?.phone || '') ||
            formData.profile.timezone !== (dbData.profile?.timezone || '')
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const errs = validate();
        if (Object.keys(errs).length > 0) {
            setErrors(errs);
            return;
        }
        setErrors({});
        if (!hasChanges()) {
            setStatus('no-changes');
            setTimeout(() => setStatus('idle'), 3000);
            return;
        }
        setStatus('saving');
        await new Promise(r => setTimeout(r, 500));
        try {
            const res = await axiosInstance.put('/auth/me/', formData);
            setdbData(res.data);
            setStatus('success');
            setTimeout(() => setStatus('idle'), 3000);
        } catch (err) {
            setStatus('idle');
            console.error(err);
        }
    };

    useEffect(() => {
        setLoading(true);
        axiosInstance
            .get('/auth/me/')
            .then(res => {
                setdbData(res.data);
                setFormData({
                    first_name: res.data.first_name || "",
                    last_name: res.data.last_name || "",
                    profile: {
                        display_name: res.data.profile?.display_name || "",
                        notification_email: res.data.profile?.notification_email || "",
                        phone: res.data.profile?.phone || "",
                        timezone: res.data.profile?.timezone || ""
                    }
                });
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const initials = [dbData?.first_name, dbData?.last_name]
        .filter(Boolean)
        .map(n => n[0].toUpperCase())
        .join('') || dbData?.email?.[0]?.toUpperCase() || '?';

    return (
        <div className="profile-card">
            <h2>Account Settings</h2>
            <div className="profile-card__header">
                <div className="profile-avatar">{initials}</div>
                <div className="profile-card__header-info">
                    <span className="profile-email">{dbData?.email}</span>
                    <span className="profile-member-since">
                        Member since {dbData?.date_joined ? new Date(dbData.date_joined).getFullYear() : '—'}
                    </span>
                </div>
            </div>
            <div className="profile-card__body">
                <form className="user-detail-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>First Name</label>
                        <input
                            type="text"
                            value={formData.first_name}
                            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        />
                        {errors.first_name && <span className="form-error">{errors.first_name}</span>}
                    </div>
                    <div className="form-group">
                        <label>Last Name</label>
                        <input
                            type="text"
                            value={formData.last_name}
                            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        />
                        {errors.last_name && <span className="form-error">{errors.last_name}</span>}
                    </div>
                    <div className="form-group">
                        <label>Display Name</label>
                        <input
                            type="text"
                            value={formData.profile.display_name}
                            onChange={(e) => setFormData({...formData, profile: {...formData.profile, display_name: e.target.value}})}
                        />
                    </div>
                    <div className="form-group">
                        <label>Notification Email</label>
                        <input
                            type="text"
                            value={formData.profile.notification_email}
                            onChange={(e) => setFormData({...formData, profile: {...formData.profile, notification_email: e.target.value}})}
                        />
                        {errors.notification_email && <span className="form-error">{errors.notification_email}</span>}
                    </div>
                    <div className="form-group">
                        <label>Phone</label>
                        <PhoneInput
                            key={phoneKey}
                            country={phoneCountry}
                            value={formData.profile.phone}
                            onChange={(phone, countryData) => {
                                if (countryData.countryCode !== phoneCountry) {
                                    setPhoneCountry(countryData.countryCode);
                                    setPhoneKey(prev => prev + 1);
                                    setFormData(prev => ({...prev, profile: {...prev.profile, phone: ''}}));
                                    setTimeout(() => phoneInputRef.current?.focus(), 0);
                                } else {
                                    setFormData(prev => ({...prev, profile: {...prev.profile, phone}}));
                                }
                            }}
                            inputProps={{ ref: phoneInputRef }}
                            inputClass="phone-input"
                            buttonClass="phone-button"
                            dropdownClass="phone-dropdown"
                            countryCodeEditable={false}
                            masks={{ br: '(..) .....-....' }}
                        />
                        {errors.phone && <span className="form-error">{errors.phone}</span>}
                    </div>
                    <div className="form-group">
                        <label>Timezone</label>
                        <TimezoneSelect
                            value={formData.profile.timezone}
                            onChange={(tz) => setFormData({...formData, profile: {...formData.profile, timezone: tz.value}})}
                            menuPortalTarget={document.body}
                            menuPosition="fixed"
                            classNamePrefix="tz-select"
                            styles={{
                                control: (base) => ({
                                    ...base,
                                    background: 'var(--input-bg)',
                                    borderColor: 'var(--border-color)',
                                    color: 'var(--text-color)',
                                    boxShadow: 'none',
                                    '&:hover': { borderColor: 'var(--button-bg)' }
                                }),
                                menu: (base) => ({
                                    ...base,
                                    background: 'var(--input-bg)',
                                    border: '1px solid var(--border-color)',
                                    zIndex: 9999,
                                }),
                                option: (base, { isFocused }) => ({
                                    ...base,
                                    background: isFocused ? 'var(--button-bg)' : 'transparent',
                                    color: isFocused ? 'var(--button-text)' : 'var(--text-color)',
                                }),
                                singleValue: (base) => ({ ...base, color: 'var(--text-color)' }),
                                input: (base) => ({ ...base, color: 'var(--text-color)' }),
                                menuPortal: (base) => ({ ...base, zIndex: 9999 }),
                            }}
                        />
                    </div>
                    <button className={`profile-button ${!hasChanges() ? 'profile-button--unchanged' : ''}`} type="submit" disabled={status === 'saving'}>
                        {status === 'saving' ? 'Saving...' : 'Save'}
                    </button>
                    {status === 'success' && (
                        <p className="profile-success">Profile updated successfully</p>
                    )}
                    {status === 'no-changes' && (
                        <p className="profile-no-changes">No changes to save</p>
                    )}
                </form>
            </div>
        </div>
    );
};

export default UserDetailCard;
